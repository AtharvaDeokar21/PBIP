# Recommendations API

Exposes personalised product recommendations to the customer (**UC-02** dashboard recommendations, **UC-06 / UC-07 / UC-12**).

> Conventions, authentication and error formats: see the [Customer API overview](README.md).

| Method | Path | Role |
|---|---|---|
| `GET` | `/api/v1/recommendations` | CUSTOMER |

### Ownership boundary
The **Internal/Analytics team** generates recommendations: they write rows to the `recommendations` table from behavioural, spending and risk data. The customer module **only exposes** them, read-only, and contains no recommendation algorithm.

---

## GET /recommendations

Returns the customer's **active, unexpired** recommendations, highest score first. A recommendation is included when:
- it belongs to the authenticated customer,
- its `status` is `ACTIVE`, and
- `expires_at` is empty or in the future.

| Query param | Type | Constraints | Description |
|---|---|---|---|
| `product_type` | string | ≤ 50 chars | Case-insensitive exact match: `LOAN`, `INVESTMENT`, `INSURANCE`, `SAVINGS`, `CREDIT` |

**Response `200`:** array of `RecommendationResponse`.
```json
[
  {
    "id": "81cdff74-4a6d-4e62-81ce-c76cb2198d5e",
    "product_type": "INVESTMENT",
    "product_id": "7ffee6cb-a251-4748-8bf4-53fc99f61475",
    "recommendation_type": "CROSS_SELL",
    "score": "0.8500",
    "reason": "Regular surplus balance suits a balanced fund.",
    "status": "ACTIVE",
    "created_at": "2026-10-04T07:43:11.568507Z",
    "expires_at": "2026-11-03T07:43:11.568507Z"
  }
]
```
An empty array means there are currently no recommendations.

| Field | Type | Description |
|---|---|---|
| `id` | UUID | |
| `product_type` | string | `LOAN`, `INVESTMENT`, `INSURANCE`, `SAVINGS`, `CREDIT` |
| `product_id` | UUID | Id of the recommended product. Resolve it with the matching catalogue endpoint (see below). |
| `recommendation_type` | string | Set by the recommendation engine, for example `CROSS_SELL`, `UPSELL`, `NEXT_BEST_ACTION` |
| `score` | decimal string | Relevance / confidence score, 0–1 |
| `reason` | string \| null | Customer-facing explanation |
| `status` | string | Always `ACTIVE` in this response |
| `created_at` | timestamp | |
| `expires_at` | timestamp \| null | |

### Resolving `product_id`
| `product_type` | Lookup endpoint |
|---|---|
| `LOAN` | `GET /loans/products/{product_id}` |
| `INVESTMENT` | `GET /investments/products/{product_id}` |
| `INSURANCE` | `GET /insurance/products/{product_id}` |

---

**Source:** `app/api/recommendations.py`, `app/services/recommendation_service.py`, `app/schemas/recommendation.py`. Demo recommendations are seeded by `scripts/seed.py` (`seed_recommendations`).
