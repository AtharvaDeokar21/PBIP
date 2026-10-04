# Customers API

The authenticated customer's own profile and a consolidated financial summary that powers the dashboard (**UC-02**).

> Conventions, authentication and error formats: see the [Customer API overview](README.md).

| Method | Path | Role |
|---|---|---|
| `GET` | `/api/v1/customers/me` | CUSTOMER |
| `PATCH` | `/api/v1/customers/me` | CUSTOMER |
| `GET` | `/api/v1/customers/me/summary` | CUSTOMER |

There is no `/customers/{id}` endpoint for customers. The profile is always resolved from the JWT, so a customer can never read another customer's profile.

---

## GET /customers/me

Returns the authenticated customer's profile. The email comes from the linked user account, because that's where it's stored.

**Request:** no parameters.

**Response `200`: `CustomerResponse`**
```json
{
  "id": "befceb28-3095-4413-bade-f870058cfcde",
  "customer_number": "CUST000001",
  "first_name": "Atharva",
  "last_name": "Deokar",
  "email": "customer@pbip.demo",
  "phone": "+919999999999",
  "address": "12 MG Road, Kothrud",
  "city": "Pune",
  "state": "Maharashtra",
  "postal_code": "411038",
  "occupation": "Software Engineer",
  "employment_type": "FULL_TIME",
  "annual_income": "1200000.00",
  "risk_profile": "MODERATE",
  "customer_segment": "MASS_AFFLUENT"
}
```

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Customer id |
| `customer_number` | string | Business identifier (for example `CUST000001`, or `PBIP-…` for self-registered customers) |
| `first_name`, `last_name` | string | |
| `email` | string | Login email of the linked user |
| `phone` | string \| null | |
| `address`, `city`, `state`, `postal_code` | string \| null | |
| `occupation` | string \| null | |
| `employment_type` | string \| null | For example `FULL_TIME`, `SELF_EMPLOYED`, `CONTRACT` |
| `annual_income` | decimal string \| null | Bank-maintained; used for loan eligibility |
| `risk_profile` | string \| null | `LOW`, `MODERATE`, `HIGH` |
| `customer_segment` | string \| null | `MASS_MARKET`, `MASS_AFFLUENT`, `AFFLUENT`, `HIGH_NET_WORTH` |

**Errors:** `401`, `403`, `404 Customer profile not found`.

---

## PATCH /customers/me

Partially updates the customer's **self-service** fields. Fields you leave out stay unchanged; a field sent as `null` is cleared.

Financial and classification fields (`annual_income`, `employment_type`, `risk_profile`, `customer_segment`), as well as identity fields (`first_name`, `last_name`, `customer_number`), are **bank-controlled and can't be edited** here. Sending any of them returns `422`.

**Request body: `CustomerUpdate`** (all fields optional)

| Field | Type | Constraints |
|---|---|---|
| `phone` | string | `^\+?[0-9]{10,15}$` |
| `address` | string | 1–500 chars |
| `city` | string | 1–100 chars |
| `state` | string | 1–100 chars |
| `postal_code` | string | `^[0-9A-Za-z\- ]{3,20}$` |
| `occupation` | string | 1–150 chars |

Leading and trailing whitespace is trimmed. Unknown fields are rejected.

```json
{
  "address": "12 MG Road, Kothrud",
  "city": "Pune",
  "state": "Maharashtra",
  "postal_code": "411038"
}
```

**Response `200`:** the updated `CustomerResponse` (same shape as `GET /customers/me`).

**Side effects:** when at least one value actually changes, an audit entry `CUSTOMER_PROFILE_UPDATED` is written, recording the old and new values of the changed fields only. A request that changes nothing writes no audit entry.

**Errors:**
| Status | When |
|---|---|
| `422` | Field fails validation, or a non-editable / unknown field was sent (`Extra inputs are not permitted`) |
| `401` / `403` / `404` | See the overview |

---

## GET /customers/me/summary

A consolidated financial overview for the dashboard, calculated live from the customer's accounts, transactions, payees, loan applications and investments.

**Request:** no parameters.

**Response `200`: `CustomerSummary`**
```json
{
  "currency": "INR",
  "total_balance": "228000.00",
  "total_available_balance": "228000.00",
  "total_accounts": 2,
  "active_accounts": 2,
  "balances_by_type": [
    { "account_type": "SAVINGS", "balance": "142000.00", "account_count": 1 },
    { "account_type": "CURRENT", "balance": "86000.00", "account_count": 1 }
  ],
  "month_to_date_credits": "1000.00",
  "month_to_date_debits": "22000.00",
  "active_payees": 1,
  "open_loan_applications": 1,
  "total_invested": "10000.00"
}
```

| Field | Description |
|---|---|
| `currency` | Reporting currency (`INR`) |
| `total_balance` | Sum of `balance` across all the customer's accounts |
| `total_available_balance` | Sum of `available_balance` across all accounts |
| `total_accounts` | Number of accounts of any status |
| `active_accounts` | Accounts with status `ACTIVE` |
| `balances_by_type[]` | Balance and account count per `account_type` |
| `month_to_date_credits` | Sum of `COMPLETED` `CREDIT` transactions since 00:00 UTC on the 1st of the current month |
| `month_to_date_debits` | Same, for `DEBIT` transactions |
| `active_payees` | Number of active (non-deactivated) payees |
| `open_loan_applications` | Applications with status `SUBMITTED` or `UNDER_REVIEW` |
| `total_invested` | Sum of `amount_invested` over `ACTIVE` investment holdings |

**Errors:** `401`, `403`, `404`.

---

**Source:** `app/api/customers.py`, `app/services/customer_service.py`, `app/schemas/customer.py`
