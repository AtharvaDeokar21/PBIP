# Accounts & Transactions API

Read access to the customer's bank accounts and their transaction history, with search and filtering (**Account Services** and **UC-02**).

> Conventions, authentication and error formats: see the [Customer API overview](README.md).

| Method | Path | Role |
|---|---|---|
| `GET` | `/api/v1/accounts` | CUSTOMER |
| `GET` | `/api/v1/accounts/{account_id}` | CUSTOMER |
| `GET` | `/api/v1/accounts/{account_id}/transactions` | CUSTOMER |
| `GET` | `/api/v1/transactions/{transaction_id}` | CUSTOMER |

These APIs are **read-only**. Balances change only as a side effect of [transfers](transfers.md), [bill payments](bills.md) and [investment purchases](investments.md).

---

## The Account object

```json
{
  "id": "849a45f2-21e6-4eac-b6e6-e48a8db3b2b1",
  "account_number": "XXXX08ab",
  "account_type": "SAVINGS",
  "currency": "INR",
  "balance": "150000.00",
  "available_balance": "150000.00",
  "status": "ACTIVE",
  "opened_at": "2025-11-12T09:30:00Z",
  "created_at": "2026-10-04T07:43:11Z"
}
```

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Account id. Use it in all requests. |
| `account_number` | string | **Masked**: only the last 4 characters are shown (`XXXX` + last 4) |
| `account_type` | string | `SAVINGS`, `CURRENT`, `CREDIT`, `INVESTMENT` |
| `currency` | string | ISO-4217 code, normally `INR` |
| `balance` | decimal string | Ledger balance |
| `available_balance` | decimal string | Spendable balance. **All debits are checked against this.** |
| `status` | string | `ACTIVE`, or another status such as `FROZEN` or `CLOSED`. Only `ACTIVE` accounts can be debited or credited. |
| `opened_at` | timestamp \| null | Account opening date |
| `created_at` | timestamp | Record creation time |

---

## GET /accounts

Lists every account belonging to the authenticated customer, oldest first.

**Response `200`: `AccountListResponse`**
```json
{
  "items": [
    {
      "id": "849a45f2-21e6-4eac-b6e6-e48a8db3b2b1",
      "account_number": "XXXX08ab",
      "account_type": "SAVINGS",
      "currency": "INR",
      "balance": "150000.00",
      "available_balance": "150000.00",
      "status": "ACTIVE",
      "opened_at": null,
      "created_at": "2026-10-04T07:43:11Z"
    },
    {
      "id": "0b7e5f21-f489-4700-9974-05266ebd4d07",
      "account_number": "XXXX0426",
      "account_type": "CURRENT",
      "currency": "INR",
      "balance": "85000.00",
      "available_balance": "85000.00",
      "status": "ACTIVE",
      "opened_at": null,
      "created_at": "2026-10-04T07:43:11Z"
    }
  ],
  "total": 2
}
```
A customer with no accounts gets `{"items": [], "total": 0}`.

---

## GET /accounts/{account_id}

Returns one account.

| Path param | Type | Description |
|---|---|---|
| `account_id` | UUID | Must belong to the authenticated customer |

**Response `200`:** an [Account object](#the-account-object).

**Errors:**
| Status | `detail` | When |
|---|---|---|
| `404` | `Account not found` | The id doesn't exist **or belongs to another customer** |
| `422` | validation list | `account_id` is not a valid UUID |

---

## GET /accounts/{account_id}/transactions

Paginated transaction history for one of the customer's accounts, newest first (ordered by `transaction_date` descending). Supports filtering and free-text search.

| Path param | Type | Description |
|---|---|---|
| `account_id` | UUID | Must belong to the authenticated customer |

**Query parameters** (all optional; filters are combined with AND)

| Param | Type | Constraints | Behaviour |
|---|---|---|---|
| `page` | int | ≥ 1, default `1` | |
| `page_size` | int | 1–100, default `20` | |
| `category` | string | ≤ 80 chars | Exact match, case-insensitive. For example `GROCERIES`, `DINING`, `SALARY`, `TRANSFER`, `BILL_PAYMENT`, `INVESTMENT` |
| `transaction_type` | string | ≤ 40 chars | `DEBIT` or `CREDIT`, case-insensitive |
| `transaction_status` | string | ≤ 30 chars | For example `COMPLETED`, `PENDING`, `FAILED`, case-insensitive |
| `start_date` | date | `YYYY-MM-DD`, must be ≤ `end_date` | Inclusive, from 00:00 UTC |
| `end_date` | date | `YYYY-MM-DD` | Inclusive, until the end of that UTC day |
| `min_amount` | decimal | ≥ 0, must be ≤ `max_amount` | Inclusive |
| `max_amount` | decimal | ≥ 0 | Inclusive |
| `search` | string | 1–100 chars | Case-insensitive *contains* match on `description`, `merchant_name` or `transaction_reference`. Wildcard characters (`%`, `_`) are matched literally. |

Unknown query parameters are rejected with `422`.

**Example:** `GET /api/v1/accounts/849a45f2-…/transactions?transaction_type=DEBIT&category=groceries&page=1&page_size=20`

**Response `200`: `Page[TransactionResponse]`**
```json
{
  "items": [
    {
      "id": "55d9ab41-dab5-40dc-9947-30630d3acf18",
      "account_id": "849a45f2-21e6-4eac-b6e6-e48a8db3b2b1",
      "transaction_reference": "TXNF1DD474722F2",
      "transaction_type": "DEBIT",
      "amount": "2500.00",
      "currency": "INR",
      "category": "GROCERIES",
      "description": "Groceries transaction",
      "merchant_name": "Fresh Mart",
      "merchant_category": "GROCERIES",
      "transaction_status": "COMPLETED",
      "transaction_date": "2026-10-04T07:43:11.515425Z",
      "location": null,
      "channel": "MOBILE"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 3
}
```

**Errors:**
| Status | `detail` | When |
|---|---|---|
| `404` | `Account not found` | Account doesn't exist or isn't owned by the caller |
| `422` | `start_date must be on or before end_date` | Invalid date range |
| `422` | `min_amount must be less than or equal to max_amount` | Invalid amount range |
| `422` | validation list | `page_size` > 100, negative amount, `search` too long, unknown parameter |

---

## GET /transactions/{transaction_id}

Returns one transaction. Ownership is checked through the transaction's account.

| Path param | Type | Description |
|---|---|---|
| `transaction_id` | UUID | Must belong to one of the caller's accounts |

**Response `200`:** a [Transaction object](#the-transaction-object).

**Errors:** `404 Transaction not found` if it doesn't exist or isn't owned by the caller.

There is no unscoped `GET /transactions` listing. History is always read per account, through `/accounts/{account_id}/transactions`.

---

## The Transaction object

| Field | Type | Description |
|---|---|---|
| `id` | UUID | |
| `account_id` | UUID | Owning account |
| `transaction_reference` | string | Unique reference. Transactions created by this API use the format `TXN-YYYYMMDD-XXXXXXXXXXXX`. |
| `transaction_type` | string | `DEBIT` (money out) or `CREDIT` (money in) |
| `amount` | decimal string | Always positive; the direction is given by `transaction_type` |
| `currency` | string | |
| `category` | string \| null | Spending category |
| `description` | string \| null | Human-readable description, for example `Transfer TRF-… to Rahul Sharma (XXXX9012) - Dinner split` |
| `merchant_name` | string \| null | Merchant or counterparty (the biller name for bill payments, the product name for investments) |
| `merchant_category` | string \| null | |
| `transaction_status` | string | `COMPLETED` for everything created by this API |
| `transaction_date` | timestamp | When the transaction happened |
| `location` | string \| null | |
| `channel` | string \| null | `ONLINE` for API-originated transactions; `MOBILE`, `WEB`, `ATM`, `CARD`, `UPI`, etc. for imported data |

Internal fraud-model fields (`is_fraud`, `latitude`, `longitude`) are deliberately **not exposed** to customers.

---

**Source:** `app/api/accounts.py`, `app/api/transactions.py`, `app/services/account_service.py`, `app/services/transaction_service.py`, `app/schemas/account.py`, `app/schemas/transaction.py`
