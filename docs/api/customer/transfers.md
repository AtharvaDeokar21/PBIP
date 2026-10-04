# Transfers API

Move money from a customer's account to a saved payee or to another of the customer's own accounts, immediately or on a schedule (**UC-04 Transfer Money**, **Scheduled transfers**).

> Conventions, authentication and error formats: see the [Customer API overview](README.md).

| Method | Path | Role |
|---|---|---|
| `POST` | `/api/v1/transfers` | CUSTOMER |
| `GET` | `/api/v1/transfers` | CUSTOMER |
| `GET` | `/api/v1/transfers/{transfer_id}` | CUSTOMER |
| `POST` | `/api/v1/transfers/{transfer_id}/cancel` | CUSTOMER |

---

## Transfer kinds

| Kind | Target field | Money movement |
|---|---|---|
| **Payee transfer** | `payee_id` | Source account is debited. The payee is treated as an external account. |
| **Internal transfer** | `destination_account_id` | Source is debited and the customer's own destination account is credited, in the same DB transaction |

| Timing | `transfer_type` | Behaviour |
|---|---|---|
| **Immediate** | `IMMEDIATE` (default) | Executed synchronously; the response already shows `COMPLETED` |
| **Scheduled** | `SCHEDULED` | Stored with status `SCHEDULED`; **no money moves at creation** |

**Scheduled execution is not yet implemented.** Scheduled transfers can be created, listed and cancelled, but no background job executes them at `scheduled_at` yet. When one is added, it must re-run the balance and limit checks at execution time and use the state machine below (`SCHEDULED → PROCESSING → COMPLETED/FAILED`).

---

## Status lifecycle

```
                     ┌──────────► CANCELLED ◄───────────┐
                     │ (customer cancel)                 │ (customer cancel)
 IMMEDIATE:  PENDING ──► PROCESSING ──► COMPLETED        │
                │              └──────► FAILED           │
                └──► FAILED                              │
 SCHEDULED:  SCHEDULED ──► PROCESSING ──► COMPLETED / FAILED
                 └───────────────────────────────────────┘
```

| From | Allowed transitions |
|---|---|
| `PENDING` | `PROCESSING`, `CANCELLED`, `FAILED` |
| `SCHEDULED` | `PROCESSING`, `CANCELLED` |
| `PROCESSING` | `COMPLETED`, `FAILED` |
| `COMPLETED`, `FAILED`, `CANCELLED` | none (terminal) |

Transitions are enforced in `payment_service.transition()`. Clients **can't set a status**; the only state change a customer can trigger is cancellation of a `PENDING` or `SCHEDULED` transfer.

---

## The Transfer object

```json
{
  "id": "c347b08c-c1a0-464d-a5bf-e9e0e7d7f2f9",
  "source_account_id": "849a45f2-21e6-4eac-b6e6-e48a8db3b2b1",
  "destination_account_id": null,
  "payee_id": "ce589082-8c4c-43fb-8713-c36d3e3023cf",
  "amount": "500.00",
  "transfer_type": "IMMEDIATE",
  "status": "COMPLETED",
  "reference_number": "TRF-20261004-A10C62371240",
  "scheduled_at": null,
  "executed_at": "2026-10-04T07:43:12.137680Z",
  "created_at": "2026-10-04T07:43:12Z"
}
```

| Field | Type | Description |
|---|---|---|
| `id` | UUID | |
| `source_account_id` | UUID | Debited account |
| `destination_account_id` | UUID \| null | Set for internal transfers |
| `payee_id` | UUID \| null | Set for payee transfers |
| `amount` | decimal string | |
| `transfer_type` | string | `IMMEDIATE` or `SCHEDULED` |
| `status` | string | See the [lifecycle](#status-lifecycle) |
| `reference_number` | string | Unique, non-guessable reference: `TRF-YYYYMMDD-<12 hex>` |
| `scheduled_at` | timestamp \| null | Execution time for scheduled transfers |
| `executed_at` | timestamp \| null | When the money moved |
| `created_at` | timestamp | |

---

## POST /transfers

Creates a transfer.

**Request body: `TransferCreate`**

| Field | Type | Required | Constraints |
|---|---|---|---|
| `source_account_id` | UUID | ✅ | Must be owned by the caller and `ACTIVE` |
| `payee_id` | UUID | one of these two | Must be owned by the caller and active |
| `destination_account_id` | UUID | one of these two | Must be owned by the caller, `ACTIVE`, the same currency as the source, and different from the source |
| `amount` | decimal | ✅ | > 0, at most 2 decimal places, ≤ the per-transfer limit |
| `transfer_type` | enum | | `IMMEDIATE` (default) or `SCHEDULED` |
| `scheduled_at` | datetime | for `SCHEDULED` only | Must be in the future and at most 365 days ahead. A time without a timezone is treated as UTC. Not allowed for `IMMEDIATE`. |
| `remarks` | string | | ≤ 200 chars; included in the ledger description |

**Immediate payee transfer**
```json
{
  "source_account_id": "849a45f2-21e6-4eac-b6e6-e48a8db3b2b1",
  "payee_id": "ce589082-8c4c-43fb-8713-c36d3e3023cf",
  "amount": 5000,
  "transfer_type": "IMMEDIATE",
  "remarks": "Rent share"
}
```

**Internal transfer between own accounts**
```json
{
  "source_account_id": "849a45f2-21e6-4eac-b6e6-e48a8db3b2b1",
  "destination_account_id": "0b7e5f21-f489-4700-9974-05266ebd4d07",
  "amount": 1000
}
```

**Scheduled transfer**
```json
{
  "source_account_id": "849a45f2-21e6-4eac-b6e6-e48a8db3b2b1",
  "payee_id": "ce589082-8c4c-43fb-8713-c36d3e3023cf",
  "amount": 5000,
  "transfer_type": "SCHEDULED",
  "scheduled_at": "2026-10-15T10:00:00"
}
```

### Processing steps
All steps run in a single database transaction. Validation (steps 1–6) finishes before anything is written, so a rejected transfer leaves no trace apart from the error response.

1. **Authenticate** the caller and resolve the customer from the JWT.
2. **Lock and verify the accounts:** the source (and the destination, for internal transfers) are fetched with `SELECT … FOR UPDATE`, filtered by the caller's `customer_id`, and locked in a fixed order.
3. **Check the source account** is `ACTIVE`.
4. **Check the target:**
   - internal transfer: the destination is `ACTIVE` and in the same currency;
   - payee transfer: the payee belongs to the caller and is active.
5. **Check limits:**
   - per transfer: `amount ≤ MAX_SINGLE_TRANSFER_AMOUNT` (₹5,00,000);
   - per day: today's total plus `amount` must be ≤ `DAILY_TRANSFER_LIMIT` (₹10,00,000). Today's total covers the caller's transfers created since 00:00 UTC with status `PENDING`, `PROCESSING`, `COMPLETED` or `SCHEDULED`; cancelled and failed transfers don't count, while scheduled ones count on the day they were created.
6. **Check funds:** `available_balance ≥ amount`. This applies to scheduled transfers too, at creation time.
7. **Create** the transfer record, with a generated `reference_number`.
8. **Immediate transfers only:**
   - status goes `PENDING → PROCESSING`;
   - the source's `balance` and `available_balance` are debited, and a `DEBIT` ledger transaction is created (category `TRANSFER`);
   - for internal transfers, the destination is credited and a `CREDIT` ledger transaction is created;
   - status goes `PROCESSING → COMPLETED` and `executed_at` is set.
9. **Audit:** `TRANSFER_CREATED`, plus `TRANSFER_COMPLETED` for immediate transfers.
10. **Notify:** `TRANSFER_COMPLETED`, or `TRANSFER_SCHEDULED`.
11. **Flag for fraud monitoring:** if `amount ≥ ₹2,00,000`, a `HIGH_VALUE_TRANSFER` security event (severity `WARNING`) is recorded.
12. **Commit.**

**Response `201`:** the [Transfer object](#the-transfer-object). Immediate transfers come back as `COMPLETED`, scheduled ones as `SCHEDULED`.

**Errors**
| Status | `detail` | Cause |
|---|---|---|
| `404` | `Account not found` | Source or destination doesn't exist or isn't owned by the caller |
| `404` | `Payee not found` | Payee doesn't exist, isn't owned by the caller, or is deactivated |
| `422` | `Account is not active` | Source or destination status isn't `ACTIVE` |
| `422` | `Cross-currency transfers are not supported` | Source and destination currencies differ |
| `422` | `Amount exceeds the per-transfer limit` | `amount` > ₹5,00,000 |
| `422` | `Amount exceeds the daily transfer limit` | The daily total would exceed ₹10,00,000 |
| `422` | `Insufficient available balance` | `available_balance` < `amount` |
| `422` | `Provide exactly one of payee_id or destination_account_id` | Both or neither given |
| `422` | `Source and destination accounts must differ` | Same account on both sides |
| `422` | `scheduled_at is required for SCHEDULED transfers` | |
| `422` | `scheduled_at must be in the future` | |
| `422` | `scheduled_at cannot be more than 1 year ahead` | |
| `422` | `scheduled_at is only allowed for SCHEDULED transfers` | `scheduled_at` sent with `IMMEDIATE` |
| `422` | validation list | `amount` ≤ 0, more than 2 decimals, invalid UUID, unknown field |

---

## GET /transfers

Paginated history of the customer's transfers, newest first.

| Query param | Type | Default | Description |
|---|---|---|---|
| `page` | int | `1` | ≥ 1 |
| `page_size` | int | `20` | 1–100 |
| `status` | enum | — | Filter: `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`, `CANCELLED`, `SCHEDULED` (exact, upper-case) |

**Response `200`: `Page[TransferResponse]`**
```json
{
  "items": [
    {
      "id": "494d1cce-a3ef-4515-b915-81f77177df2d",
      "source_account_id": "849a45f2-21e6-4eac-b6e6-e48a8db3b2b1",
      "destination_account_id": null,
      "payee_id": "ce589082-8c4c-43fb-8713-c36d3e3023cf",
      "amount": "2000.00",
      "transfer_type": "SCHEDULED",
      "status": "CANCELLED",
      "reference_number": "TRF-20261004-528E8C2D14D6",
      "scheduled_at": "2026-10-15T10:00:00Z",
      "executed_at": null,
      "created_at": "2026-10-04T07:43:12Z"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 3
}
```

---

## GET /transfers/{transfer_id}

Returns one transfer, including its current status. Clients can use this to track a transfer.

**Response `200`:** the [Transfer object](#the-transfer-object).
**Errors:** `404 Transfer not found` if it doesn't exist or isn't owned by the caller.

---

## POST /transfers/{transfer_id}/cancel

Cancels a transfer that hasn't been executed yet. There is no request body.

| Current status | Result |
|---|---|
| `SCHEDULED`, `PENDING` | → `CANCELLED` |
| anything else | `409` |

Since a scheduled transfer never reserved funds, cancelling it doesn't change any balance.

**Response `200`:** the updated [Transfer object](#the-transfer-object) with `status: "CANCELLED"`.

**Side effects:** audit entry `TRANSFER_CANCELLED` (old and new status) and notification `TRANSFER_CANCELLED`. The transfer row is locked while it's being cancelled.

**Errors**
| Status | `detail` | Cause |
|---|---|---|
| `404` | `Transfer not found` | Doesn't exist or isn't owned by the caller |
| `409` | `A COMPLETED transfer cannot be cancelled` (or `CANCELLED`, `FAILED`, `PROCESSING`) | The transfer is no longer cancellable |

---

**Source:** `app/api/transfers.py`, `app/services/payment_service.py`, `app/schemas/transfer.py`
