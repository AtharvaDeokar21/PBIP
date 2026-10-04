# Investments API

Investment product catalogue, customer holdings, and simulated investment purchases (**Wealth Management**: mutual funds, fixed deposits, stocks and bonds; **UC-07**).

> Conventions, authentication and error formats: see the [Customer API overview](README.md).

| Method | Path | Role |
|---|---|---|
| `GET` | `/api/v1/investments/products` | Any authenticated user |
| `GET` | `/api/v1/investments/products/{product_id}` | Any authenticated user |
| `GET` | `/api/v1/investments` | CUSTOMER |
| `POST` | `/api/v1/investments` | CUSTOMER |

Purchases are **simulated**: no exchange, fund house or depository is involved. A purchase records a holding and, optionally, debits one of the customer's accounts.

---

## The Investment Product object

```json
{
  "id": "7ffee6cb-a251-4748-8bf4-53fc99f61475",
  "name": "Balanced Growth Fund",
  "product_type": "MUTUAL_FUND",
  "risk_level": "MODERATE",
  "expected_return": "12.0000",
  "minimum_investment": "1000.00",
  "lock_in_period": null,
  "description": "Diversified balanced mutual fund."
}
```

| Field | Type | Description |
|---|---|---|
| `id` | UUID | |
| `name` | string | |
| `product_type` | string | For example `MUTUAL_FUND`, `BOND`, `FIXED_DEPOSIT`, `STOCK` |
| `risk_level` | string | `LOW`, `MODERATE`, `HIGH` |
| `expected_return` | decimal string \| null | Expected annual return, % |
| `minimum_investment` | decimal string | Minimum amount per purchase |
| `lock_in_period` | string \| null | For example `3 years` |
| `description` | string \| null | |

---

## GET /investments/products

Lists **active** investment products, sorted by name. The response carries comparable attributes (risk, return, minimum, lock-in), so it can feed product comparison.

| Query param | Type | Constraints | Description |
|---|---|---|---|
| `product_type` | string | ≤ 50 chars | Case-insensitive exact match |
| `risk_level` | string | ≤ 30 chars | Case-insensitive exact match |

**Response `200`:** array of [Investment Product objects](#the-investment-product-object).

## GET /investments/products/{product_id}

**Response `200`:** one [Investment Product](#the-investment-product-object).
**Errors:** `404 Investment product not found` if it doesn't exist or is inactive.

---

## GET /investments

Lists the customer's investment holdings, newest purchase first.

**Response `200`:** array of [Investment (holding) objects](#the-investment-holding-object).

---

## POST /investments

Records a simulated investment purchase.

**Request body: `InvestmentCreate`**

| Field | Type | Required | Constraints |
|---|---|---|---|
| `investment_product_id` | UUID | ✅ | An active product |
| `amount_invested` | decimal | ✅ | > 0, at most 2 decimal places, ≥ the product's `minimum_investment` |
| `source_account_id` | UUID | | If given, the account is debited. It must be owned by the caller, `ACTIVE`, and have enough available balance. |

Record a holding only (no money moves):
```json
{
  "investment_product_id": "7ffee6cb-a251-4748-8bf4-53fc99f61475",
  "amount_invested": 5000
}
```

Pay from an account:
```json
{
  "investment_product_id": "7ffee6cb-a251-4748-8bf4-53fc99f61475",
  "amount_invested": 5000,
  "source_account_id": "849a45f2-21e6-4eac-b6e6-e48a8db3b2b1"
}
```

### Processing steps (single DB transaction)
1. Check the product exists and is active.
2. Check `amount_invested ≥ minimum_investment`.
3. If `source_account_id` is given:
   - lock the account and check ownership, `ACTIVE` status and available balance;
   - debit it and create a `DEBIT` ledger transaction (category `INVESTMENT`, `merchant_name` = the product name).
4. Create the holding: status `ACTIVE`, `purchase_date` = today (UTC), `current_value` = `amount_invested`, and `units` / `purchase_price` left empty (no NAV pricing in simulation).
5. Write the audit entry `INVESTMENT_PURCHASED` and the notification `INVESTMENT_PURCHASED`.
6. Commit.

Transfer limits don't apply to investment purchases.

**Response `201`:** an [Investment (holding) object](#the-investment-holding-object).

**Errors**
| Status | `detail` | Cause |
|---|---|---|
| `404` | `Investment product not found` | Unknown or inactive product |
| `404` | `Account not found` | `source_account_id` isn't owned by the caller |
| `422` | `Minimum investment for this product is 1000.00` | Below the product minimum |
| `422` | `Account is not active` | Source account not `ACTIVE` |
| `422` | `Insufficient available balance` | |
| `422` | validation list | Invalid input or unknown field |

---

## The Investment (holding) object

```json
{
  "id": "532b282c-a665-4bf7-b7f0-c4c53bd37e3f",
  "investment_product_id": "7ffee6cb-a251-4748-8bf4-53fc99f61475",
  "amount_invested": "5000.00",
  "units": null,
  "purchase_price": null,
  "current_value": "5000.00",
  "purchase_date": "2026-10-04",
  "status": "ACTIVE"
}
```

| Field | Type | Description |
|---|---|---|
| `id` | UUID | |
| `investment_product_id` | UUID | |
| `amount_invested` | decimal string | |
| `units` | decimal string \| null | Units allotted. `null` for simulated purchases. |
| `purchase_price` | decimal string \| null | NAV or price per unit. `null` for simulated purchases. |
| `current_value` | decimal string \| null | Equal to the invested amount at purchase; can be revalued by other processes |
| `purchase_date` | date | |
| `status` | string | `ACTIVE` for new holdings |

---

**Source:** `app/api/investments.py`, `app/services/investment_service.py`, `app/schemas/investment.py`
