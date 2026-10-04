# Bills API

Biller catalogue and bill payments (**Payments & Transfers: Bill payments**).

> Conventions, authentication and error formats: see the [Customer API overview](README.md).

| Method | Path | Role |
|---|---|---|
| `GET` | `/api/v1/billers` | Any authenticated user |
| `POST` | `/api/v1/bills/pay` | CUSTOMER |
| `GET` | `/api/v1/bills/history` | CUSTOMER |

Bill payments are simulated. No real biller or payment-gateway integration exists; a payment completes synchronously against the customer's account.

---

## GET /billers

Lists **active** billers, sorted by category and then name.

| Query param | Type | Constraints | Description |
|---|---|---|---|
| `category` | string | ≤ 80 chars | Case-insensitive exact match, for example `ELECTRICITY`, `GAS`, `MOBILE`, `BROADBAND`, `WATER` |
| `provider_code` | string | ≤ 50 chars | Exact match, for example `BSES001` |

**Response `200`:** array of `BillerResponse`.
```json
[
  {
    "id": "73f90e4a-b980-4dce-94d1-b102d2e02fb5",
    "name": "BSES Electricity",
    "category": "ELECTRICITY",
    "provider_code": "BSES001",
    "is_active": true
  }
]
```

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Use it as `biller_id` when paying |
| `name` | string | Display name |
| `category` | string \| null | Biller category |
| `provider_code` | string | Unique provider code |
| `is_active` | bool | Always `true` in this listing |

---

## POST /bills/pay

Pays a bill from one of the customer's accounts.

**Request body: `BillPaymentCreate`**

| Field | Type | Required | Constraints |
|---|---|---|---|
| `account_id` | UUID | ✅ | Owned by the caller and `ACTIVE` |
| `biller_id` | UUID | ✅ | An active biller |
| `amount` | decimal | ✅ | > 0, at most 2 decimal places |
| `due_date` | date | | `YYYY-MM-DD`; stored for reference only |

```json
{
  "account_id": "849a45f2-21e6-4eac-b6e6-e48a8db3b2b1",
  "biller_id": "73f90e4a-b980-4dce-94d1-b102d2e02fb5",
  "amount": 1500,
  "due_date": "2026-10-05"
}
```

### Processing steps (single DB transaction)
1. Check the biller exists and is active.
2. Lock the account (`FOR UPDATE`), and check the caller owns it and it's `ACTIVE`.
3. Check `available_balance ≥ amount`.
4. Debit the account and create a `DEBIT` ledger transaction: category `BILL_PAYMENT`, `merchant_name` set to the biller name, description `Bill payment BILL-… to <biller>`.
5. Create the bill payment record with status `COMPLETED`, `paid_at` = now, and reference `BILL-YYYYMMDD-<12 hex>`.
6. Write the audit entry `BILL_PAYMENT_COMPLETED` (reference, masked account, biller code, amount).
7. Send the notification `BILL_PAYMENT_COMPLETED`.
8. Commit.

Transfer limits don't apply to bill payments; only the available balance is checked.

**Response `201`: `BillPaymentResponse`**
```json
{
  "id": "473e5845-89e0-4d1e-a021-25e0c788b3b0",
  "account_id": "849a45f2-21e6-4eac-b6e6-e48a8db3b2b1",
  "biller_id": "73f90e4a-b980-4dce-94d1-b102d2e02fb5",
  "amount": "1500.00",
  "status": "COMPLETED",
  "due_date": "2026-10-05T00:00:00Z",
  "paid_at": "2026-10-04T07:43:12.301867Z",
  "reference_number": "BILL-20261004-F7CFC2BE8341",
  "created_at": "2026-10-04T07:43:12Z"
}
```

| Field | Type | Description |
|---|---|---|
| `id` | UUID | |
| `account_id` | UUID | Debited account |
| `biller_id` | UUID | |
| `amount` | decimal string | |
| `status` | string | `COMPLETED` for payments made through this API (the schema also allows `PENDING` / `FAILED`) |
| `due_date` | timestamp \| null | Bill due date, as midnight UTC |
| `paid_at` | timestamp \| null | When the payment was made |
| `reference_number` | string | Payment reference |
| `created_at` | timestamp | |

**Errors**
| Status | `detail` | Cause |
|---|---|---|
| `404` | `Biller not found` | Unknown or inactive biller |
| `404` | `Account not found` | Account doesn't exist or isn't owned by the caller |
| `422` | `Account is not active` | |
| `422` | `Insufficient available balance` | |
| `422` | validation list | `amount` ≤ 0, more than 2 decimals, invalid date or UUID, unknown field |

---

## GET /bills/history

Paginated history of the customer's bill payments, newest first.

| Query param | Type | Default | Constraints |
|---|---|---|---|
| `page` | int | `1` | ≥ 1 |
| `page_size` | int | `20` | 1–100 |

**Response `200`:** `Page[BillPaymentResponse]`.
```json
{
  "items": [
    {
      "id": "473e5845-89e0-4d1e-a021-25e0c788b3b0",
      "account_id": "849a45f2-21e6-4eac-b6e6-e48a8db3b2b1",
      "biller_id": "73f90e4a-b980-4dce-94d1-b102d2e02fb5",
      "amount": "1500.00",
      "status": "COMPLETED",
      "due_date": "2026-10-05T00:00:00Z",
      "paid_at": "2026-10-04T07:43:12.301867Z",
      "reference_number": "BILL-20261004-F7CFC2BE8341",
      "created_at": "2026-10-04T07:43:12Z"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

---

**Source:** `app/api/bills.py`, `app/services/payment_service.py`, `app/schemas/bill.py`. Billers are seeded by `scripts/seed.py` (`seed_billers`).
