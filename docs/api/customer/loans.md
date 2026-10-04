# Loans API

Loan catalogue, eligibility assessment with an indicative EMI, and loan applications with tracking (**Loans** scope, **UC-06 Loan Recommendation**).

> Conventions, authentication and error formats: see the [Customer API overview](README.md).

| Method | Path | Role |
|---|---|---|
| `GET` | `/api/v1/loans/products` | Any authenticated user |
| `GET` | `/api/v1/loans/products/{product_id}` | Any authenticated user |
| `POST` | `/api/v1/loans/eligibility` | CUSTOMER |
| `POST` | `/api/v1/loans/applications` | CUSTOMER |
| `GET` | `/api/v1/loans/applications` | CUSTOMER |
| `GET` | `/api/v1/loans/applications/{application_id}` | CUSTOMER |

---

## The Loan Product object

```json
{
  "id": "890c790d-26b5-49a4-ada8-bd0a4838bd97",
  "name": "Personal Loan",
  "loan_type": "PERSONAL",
  "min_amount": "50000.00",
  "max_amount": "2000000.00",
  "interest_rate": "10.5000",
  "min_tenure_months": 12,
  "max_tenure_months": 60,
  "description": "Flexible personal loan for customers."
}
```

| Field | Type | Description |
|---|---|---|
| `id` | UUID | |
| `name` | string | |
| `loan_type` | string | For example `PERSONAL`, `HOME`, `EDUCATION` |
| `min_amount`, `max_amount` | decimal string | Allowed principal range (inclusive) |
| `interest_rate` | decimal string | **Annual** rate in percent (`10.5000` means 10.5% p.a.) |
| `min_tenure_months`, `max_tenure_months` | int | Allowed tenure range (inclusive) |
| `description` | string \| null | |

The product's internal `eligibility_rules` are deliberately not exposed.

---

## GET /loans/products

Lists **active** loan products, sorted by name.

| Query param | Type | Constraints | Description |
|---|---|---|---|
| `loan_type` | string | ≤ 50 chars | Case-insensitive exact match |

**Response `200`:** array of [Loan Product objects](#the-loan-product-object).

## GET /loans/products/{product_id}

**Response `200`:** one [Loan Product](#the-loan-product-object).
**Errors:** `404 Loan product not found` if it doesn't exist or is inactive.

---

## EMI calculation

The EMI is calculated with the standard reducing-balance formula:

```
EMI = P × r × (1 + r)^n / ((1 + r)^n − 1)

P = principal (requested_amount)
r = monthly rate = annual interest_rate / 12 / 100
n = tenure in months
```

- When the rate is 0%, `EMI = P / n`.
- The result is rounded half-up to 2 decimal places.
- The calculation uses `Decimal` throughout.

Example: ₹5,00,000 at 10.5% for 36 months gives an EMI of **₹16,251.22**.

Implemented in `loan_service.calculate_emi()`.

---

## Eligibility assessment

`loan_service.assess_eligibility()` is a pure function (no I/O) that combines:

| Input | Source |
|---|---|
| Requested amount and tenure | Request |
| Product limits and `eligibility_rules` | `loan_products` |
| Annual income | `customers.annual_income` |
| Credit score | `customer_risk_profiles.credit_score` (maintained by the Internal team; optional) |
| Existing EMI obligations | Sum of `emi_amount` over the customer's `APPROVED` loan applications |

**Checks** (any failure makes the customer ineligible):
1. The amount is within the product's `min_amount`–`max_amount`, and the tenure within `min_tenure_months`–`max_tenure_months`.
2. Income information is available.
3. The product rules, if configured:
   - `min_income`: minimum annual income;
   - `min_credit_score`: minimum credit score;
   - `max_dti`: maximum obligations-to-income ratio, which overrides the default.
4. **Affordability (FOIR):** `(existing EMIs + new EMI) / monthly income` must be ≤ 50%, or the product's `max_dti` if set.
5. **Overall score** ≥ the minimum qualifying score.

**Eligibility score:** a value from 0 to 1 (4 decimal places), weighted equally between credit quality and repayment headroom. If there's no credit score on file, a neutral value is used.

The customer only sees the outcome, the score and **generic reasons**. Weights and thresholds aren't exposed, as the use-case contract requires.

| Possible `reasons` |
|---|
| `Meets eligibility criteria` (only when eligible) |
| `Requested amount is outside the product's allowed range` |
| `Requested tenure is outside the product's allowed range` |
| `Income information is required for assessment` |
| `Income is below the product requirement` |
| `Credit profile does not meet the product requirement` |
| `Total repayment obligations exceed the affordable limit` |
| `Overall credit assessment is below the required level` |

---

## POST /loans/eligibility

Runs the eligibility assessment without creating anything. Use it for "Can I afford this loan?" checks and as an EMI calculator.

**Request body: `LoanEligibilityRequest`**

| Field | Type | Required | Constraints |
|---|---|---|---|
| `loan_product_id` | UUID | ✅ | An active loan product |
| `requested_amount` | decimal | ✅ | > 0, at most 2 decimal places |
| `tenure_months` | int | ✅ | 1–480 |

```json
{
  "loan_product_id": "890c790d-26b5-49a4-ada8-bd0a4838bd97",
  "requested_amount": 500000,
  "tenure_months": 36
}
```

**Response `200`: `LoanEligibilityResponse`**
```json
{
  "loan_product_id": "890c790d-26b5-49a4-ada8-bd0a4838bd97",
  "eligible": true,
  "eligibility_score": "0.5875",
  "interest_rate": "10.5000",
  "estimated_emi": "16251.22",
  "reasons": ["Meets eligibility criteria"]
}
```

Not eligible, still `200`:
```json
{
  "loan_product_id": "890c790d-26b5-49a4-ada8-bd0a4838bd97",
  "eligible": false,
  "eligibility_score": "0.2500",
  "interest_rate": "10.5000",
  "estimated_emi": "162512.22",
  "reasons": [
    "Requested amount is outside the product's allowed range",
    "Total repayment obligations exceed the affordable limit"
  ]
}
```

| Field | Type | Description |
|---|---|---|
| `loan_product_id` | UUID | |
| `eligible` | bool | |
| `eligibility_score` | decimal string | 0–1 |
| `interest_rate` | decimal string | Annual % applied |
| `estimated_emi` | decimal string | Indicative monthly instalment |
| `reasons` | string[] | Generic explanation(s) |

**Errors:** `404 Loan product not found`; `422` for invalid input.

---

## POST /loans/applications

Submits a loan application. Eligibility is assessed and stored with the application.

**Request body: `LoanApplicationCreate`**: same fields as the eligibility request.
```json
{
  "loan_product_id": "890c790d-26b5-49a4-ada8-bd0a4838bd97",
  "requested_amount": 500000,
  "tenure_months": 36
}
```

**Rules**
- Amount and tenure **must be within the product's limits**; otherwise the application is rejected with `422` and the reasons are joined in `detail`.
- Only **one open application per product**: a second application while one is `SUBMITTED` or `UNDER_REVIEW` returns `409`.
- Other eligibility failures (income, credit, affordability) **don't block submission**. The application is created with its calculated `eligibility_score`, and the decision is left to the bank's review process.

**Saved fields:** customer, product, requested amount, tenure, the product's interest rate, EMI, eligibility score, status `SUBMITTED`, and application date.

**Side effects:** audit entry `LOAN_APPLICATION_SUBMITTED`; notification `LOAN_APPLICATION_SUBMITTED`.

**Response `201`:** a [Loan Application object](#the-loan-application-object).

**Errors**
| Status | `detail` | Cause |
|---|---|---|
| `404` | `Loan product not found` | Unknown or inactive product |
| `409` | `An application for this product is already in progress` | Open application exists |
| `422` | e.g. `Requested amount is outside the product's allowed range` | Outside product limits |
| `422` | validation list | Invalid input |

---

## GET /loans/applications

Lists all the customer's loan applications, newest first.

**Response `200`:** array of [Loan Application objects](#the-loan-application-object).

## GET /loans/applications/{application_id}

Tracks a single application.

**Response `200`:** a [Loan Application object](#the-loan-application-object).
**Errors:** `404 Loan application not found` if it doesn't exist or isn't owned by the caller.

---

## The Loan Application object

```json
{
  "id": "abd92a65-b096-4601-bc37-6bc744cf6d44",
  "loan_product_id": "890c790d-26b5-49a4-ada8-bd0a4838bd97",
  "requested_amount": "500000.00",
  "tenure_months": 36,
  "interest_rate": "10.5000",
  "emi_amount": "16251.22",
  "eligibility_score": "0.5875",
  "status": "SUBMITTED",
  "application_date": "2026-10-04T07:43:12.382847Z",
  "approved_at": null,
  "rejection_reason": null
}
```

| Field | Type | Description |
|---|---|---|
| `id` | UUID | |
| `loan_product_id` | UUID | |
| `requested_amount` | decimal string | |
| `tenure_months` | int | |
| `interest_rate` | decimal string \| null | Rate locked at submission |
| `emi_amount` | decimal string \| null | EMI at submission |
| `eligibility_score` | decimal string \| null | Score at submission |
| `status` | string | See below |
| `application_date` | timestamp | |
| `approved_at` | timestamp \| null | Set when approved |
| `rejection_reason` | string \| null | Set when rejected |

### Application status lifecycle
```
SUBMITTED ──► UNDER_REVIEW ──► APPROVED
    │              │       └──► REJECTED
    └──────────────┴──────────► CANCELLED
```
The customer API only creates applications, in `SUBMITTED`. Review, approval and rejection are back-office actions and aren't exposed to customers. `APPROVED` applications count as existing obligations in future eligibility checks.

---

**Source:** `app/api/loans.py`, `app/services/loan_service.py`, `app/schemas/loan.py`
