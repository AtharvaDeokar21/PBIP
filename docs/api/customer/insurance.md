# Insurance API

Read-only insurance product catalogue (**Wealth Management: Insurance products**).

> Conventions, authentication and error formats: see the [Customer API overview](README.md).

| Method | Path | Role |
|---|---|---|
| `GET` | `/api/v1/insurance/products` | Any authenticated user |
| `GET` | `/api/v1/insurance/products/{product_id}` | Any authenticated user |

The current scope is the catalogue only. Purchasing, quotes, underwriting and policy management aren't implemented, as the team context specifies. Insurance can still be suggested to customers through [Recommendations](recommendations.md) (`product_type: "INSURANCE"`).

---

## The Insurance Product object

```json
{
  "id": "89fd2b3c-c757-4f42-b216-ddb11144f8bf",
  "name": "Life Secure",
  "insurance_type": "LIFE",
  "premium": "12000.00",
  "coverage_amount": "10000000.00",
  "term_years": 20,
  "risk_level": "LOW",
  "description": "Term life insurance."
}
```

| Field | Type | Description |
|---|---|---|
| `id` | UUID | |
| `name` | string | |
| `insurance_type` | string | For example `LIFE`, `HEALTH`, `MOTOR`, `HOME` |
| `premium` | decimal string | Annual premium (INR) |
| `coverage_amount` | decimal string | Sum assured (INR) |
| `term_years` | int | Policy term |
| `risk_level` | string \| null | `LOW`, `MODERATE`, `HIGH` |
| `description` | string \| null | |

---

## GET /insurance/products

Lists **active** insurance products, sorted by name.

| Query param | Type | Constraints | Description |
|---|---|---|---|
| `insurance_type` | string | ≤ 50 chars | Case-insensitive exact match |
| `risk_level` | string | ≤ 30 chars | Case-insensitive exact match |

**Response `200`:** array of [Insurance Product objects](#the-insurance-product-object).
```json
[
  {
    "id": "12dd3df6-5441-4cb4-af43-4e7295ee8878",
    "name": "Health Protect",
    "insurance_type": "HEALTH",
    "premium": "8500.00",
    "coverage_amount": "500000.00",
    "term_years": 1,
    "risk_level": "LOW",
    "description": "Health insurance coverage."
  },
  {
    "id": "89fd2b3c-c757-4f42-b216-ddb11144f8bf",
    "name": "Life Secure",
    "insurance_type": "LIFE",
    "premium": "12000.00",
    "coverage_amount": "10000000.00",
    "term_years": 20,
    "risk_level": "LOW",
    "description": "Term life insurance."
  }
]
```

## GET /insurance/products/{product_id}

**Response `200`:** one [Insurance Product](#the-insurance-product-object).
**Errors:** `404 Insurance product not found` if it doesn't exist or is inactive.

---

**Source:** `app/api/insurance.py`, `app/services/insurance_service.py`, `app/schemas/insurance.py`
