# Payees API

Manage payment beneficiaries (**UC-05 Manage Payees**). A payee is an external bank account that the customer can send [transfers](transfers.md) to.

> Conventions, authentication and error formats: see the [Customer API overview](README.md).

| Method | Path | Role |
|---|---|---|
| `POST` | `/api/v1/payees` | CUSTOMER |
| `GET` | `/api/v1/payees` | CUSTOMER |
| `PATCH` | `/api/v1/payees/{payee_id}` | CUSTOMER |
| `DELETE` | `/api/v1/payees/{payee_id}` | CUSTOMER |

---

## The Payee object

```json
{
  "id": "ce589082-8c4c-43fb-8713-c36d3e3023cf",
  "name": "Rahul Sharma",
  "account_number": "XXXX9012",
  "bank_name": "HDFC Bank",
  "ifsc_code": "HDFC0001234",
  "nickname": "Rahul",
  "is_verified": false,
  "is_active": true,
  "created_at": "2026-10-04T07:43:12Z",
  "updated_at": "2026-10-04T07:43:12Z"
}
```

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Payee id. Use it as `payee_id` in transfers. |
| `name` | string | Account holder name |
| `account_number` | string | **Masked** (`XXXX` + last 4) |
| `bank_name` | string | |
| `ifsc_code` | string | Indian Financial System Code of the branch |
| `nickname` | string | Customer's label for the payee |
| `is_verified` | bool | Verification state. **Currently always `false`**: no verification workflow has been implemented, and transfers don't require verification. |
| `is_active` | bool | `false` once the payee has been deactivated |
| `created_at`, `updated_at` | timestamp | |

### Lifecycle
```
POST /payees ──► ACTIVE (is_active=true) ──DELETE──► DEACTIVATED (is_active=false)
                    │  ▲
                    └──┘ PATCH (name / bank_name / nickname)
```
Deactivated payees are kept in the database so that historical transfers still reference them, but they are invisible to every payee endpoint (`404`) and can't be used for new transfers.

---

## POST /payees

Adds a new payee for the authenticated customer.

**Request body: `PayeeCreate`** (all fields required)

| Field | Type | Constraints |
|---|---|---|
| `name` | string | 1–150 chars |
| `account_number` | string | 9–18 digits (`^[0-9]{9,18}$`) |
| `bank_name` | string | 1–150 chars |
| `ifsc_code` | string | `^[A-Z]{4}0[A-Z0-9]{6}$`: 4 letters, a zero, then 6 letters or digits. Lowercase input is accepted and upper-cased. |
| `nickname` | string | 1–100 chars |

String fields are trimmed. Unknown fields (for example `customer_id` or `is_verified`) are rejected.

```json
{
  "name": "Rahul Sharma",
  "account_number": "123456789012",
  "bank_name": "HDFC Bank",
  "ifsc_code": "HDFC0001234",
  "nickname": "Rahul"
}
```

**Response `201`:** the created [Payee object](#the-payee-object), with `is_verified: false` and `is_active: true`.

**Side effects:** audit entry `PAYEE_CREATED`, with the account number masked.

**Errors:**
| Status | `detail` | When |
|---|---|---|
| `409` | `A payee with these bank details already exists` | The customer already has an **active** payee with the same `account_number` + `ifsc_code` |
| `422` | validation list | Missing field, bad IFSC, non-numeric or wrong-length account number, unknown field |

A deactivated payee doesn't block re-adding the same bank details; a new payee record is created.

---

## GET /payees

Lists the customer's **active** payees, sorted by `name`.

**Response `200`:** array of [Payee objects](#the-payee-object).
```json
[
  {
    "id": "ce589082-8c4c-43fb-8713-c36d3e3023cf",
    "name": "Rahul Sharma",
    "account_number": "XXXX9012",
    "bank_name": "HDFC Bank",
    "ifsc_code": "HDFC0001234",
    "nickname": "Rahul",
    "is_verified": false,
    "is_active": true,
    "created_at": "2026-10-04T07:43:12Z",
    "updated_at": "2026-10-04T07:43:12Z"
  }
]
```

---

## PATCH /payees/{payee_id}

Updates a payee's descriptive fields. Bank details (`account_number`, `ifsc_code`) are **immutable**: a change of bank account must be made by adding a new payee, so that a trusted beneficiary can't be silently redirected.

**Request body: `PayeeUpdate`** (all fields optional)

| Field | Type | Constraints |
|---|---|---|
| `name` | string | 1–150 chars |
| `bank_name` | string | 1–150 chars |
| `nickname` | string | 1–100 chars |

Omitted fields and fields sent as `null` are left unchanged. An empty body `{}` returns the payee unchanged.

```json
{ "nickname": "Rahul HDFC" }
```

**Response `200`:** the updated [Payee object](#the-payee-object).

**Side effects:** audit entry `PAYEE_UPDATED`, with old and new values (only written when something changes).

**Errors:**
| Status | `detail` | When |
|---|---|---|
| `404` | `Payee not found` | Doesn't exist, isn't owned by the caller, or is deactivated |
| `422` | validation list | Invalid value, or an attempt to change `account_number` / `ifsc_code` (unknown field) |

---

## DELETE /payees/{payee_id}

Deactivates a payee (soft delete). It disappears from `GET /payees` and can no longer receive transfers. Transfer history that references it is kept.

**Response `204`:** empty body.

**Side effects:** audit entry `PAYEE_DEACTIVATED` (`is_active: true → false`).

**Errors:** `404 Payee not found` (also returned on a second delete, because the payee is no longer active).

Deleting a payee doesn't cancel scheduled transfers that already target it. Cancel those separately with `POST /transfers/{id}/cancel`.

---

**Source:** `app/api/payees.py`, `app/services/payee_service.py`, `app/schemas/payee.py`; migration `a3c1f2d4e5b6_add_payee_is_active.py`
