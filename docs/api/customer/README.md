# PBIP Customer Banking API

Reference documentation for the customer-facing banking APIs owned by the **Customer team**. These APIs cover the *Customer-Facing Portal* scope of the PBIP use case document: account services, payments and transfers, loans, wealth management and personalised recommendations.

| | |
|---|---|
| **Base URL** | `http://<host>:8080/api/v1` (API gateway) |
| **Format** | JSON over HTTPS, UTF-8 |
| **Auth** | Bearer JWT (`Authorization: Bearer <token>`) |
| **Interactive docs** | customer-service Swagger UI at `http://<host>:8001/docs`, OpenAPI JSON at `/openapi.json` |
| **Architecture** | Served by customer-service behind the nginx API gateway: Router → Pydantic schema → Service → SQLAlchemy → PostgreSQL |

## Contents

| Document | Endpoints |
|---|---|
| [Customers](customers.md) | Profile, profile update, financial summary |
| [Accounts & Transactions](accounts-and-transactions.md) | Account list/details, transaction history, search and filters |
| [Payees](payees.md) | Add, list, edit and deactivate beneficiaries |
| [Transfers](transfers.md) | Immediate, internal and scheduled transfers, cancellation, history |
| [Bills](bills.md) | Biller catalogue, bill payment, payment history |
| [Loans](loans.md) | Loan catalogue, eligibility check, EMI, applications |
| [Investments](investments.md) | Investment catalogue, holdings, simulated purchase |
| [Insurance](insurance.md) | Insurance catalogue |
| [Recommendations](recommendations.md) | Personalised product recommendations (read-only) |

---

## 1. Endpoint index

| Method | Path | Role | Summary |
|---|---|---|---|
| `GET` | `/customers/me` | CUSTOMER | Get own profile |
| `PATCH` | `/customers/me` | CUSTOMER | Update editable profile fields |
| `GET` | `/customers/me/summary` | CUSTOMER | Financial summary (dashboard) |
| `GET` | `/accounts` | CUSTOMER | List own accounts |
| `GET` | `/accounts/{account_id}` | CUSTOMER | Account details |
| `GET` | `/accounts/{account_id}/transactions` | CUSTOMER | Paginated, filterable transaction history |
| `GET` | `/transactions/{transaction_id}` | CUSTOMER | Transaction details |
| `POST` | `/payees` | CUSTOMER | Add a payee |
| `GET` | `/payees` | CUSTOMER | List active payees |
| `PATCH` | `/payees/{payee_id}` | CUSTOMER | Edit a payee |
| `DELETE` | `/payees/{payee_id}` | CUSTOMER | Deactivate a payee |
| `POST` | `/transfers` | CUSTOMER | Create an immediate or scheduled transfer |
| `GET` | `/transfers` | CUSTOMER | Paginated transfer history |
| `GET` | `/transfers/{transfer_id}` | CUSTOMER | Transfer details and status |
| `POST` | `/transfers/{transfer_id}/cancel` | CUSTOMER | Cancel a pending or scheduled transfer |
| `GET` | `/billers` | Any authenticated | Active billers |
| `POST` | `/bills/pay` | CUSTOMER | Pay a bill |
| `GET` | `/bills/history` | CUSTOMER | Paginated bill payment history |
| `GET` | `/loans/products` | Any authenticated | Active loan products |
| `GET` | `/loans/products/{product_id}` | Any authenticated | Loan product details |
| `POST` | `/loans/eligibility` | CUSTOMER | Eligibility check with indicative EMI |
| `POST` | `/loans/applications` | CUSTOMER | Submit a loan application |
| `GET` | `/loans/applications` | CUSTOMER | List own applications |
| `GET` | `/loans/applications/{application_id}` | CUSTOMER | Application details and status |
| `GET` | `/investments/products` | Any authenticated | Active investment products |
| `GET` | `/investments/products/{product_id}` | Any authenticated | Investment product details |
| `GET` | `/investments` | CUSTOMER | Own investment holdings |
| `POST` | `/investments` | CUSTOMER | Record a (simulated) investment purchase |
| `GET` | `/insurance/products` | Any authenticated | Active insurance products |
| `GET` | `/insurance/products/{product_id}` | Any authenticated | Insurance product details |
| `GET` | `/recommendations` | CUSTOMER | Active recommendations for the customer |

### Related endpoints owned by the platform foundation
The customer APIs depend on these existing authentication endpoints. They are not part of this module but are listed for completeness.

| Method | Path | Summary |
|---|---|---|
| `POST` | `/auth/register` | Register a new customer (creates a `users` and a `customers` row) |
| `POST` | `/auth/login` | Exchange email and password for a JWT access token |
| `GET` | `/me` | Identity of the authenticated user (id, email, role) |

---

## 2. Authentication and authorization

### Obtaining a token
`POST /auth/login`
```json
{ "email": "customer@pbip.demo", "password": "PBIP@Demo123" }
```
Response `200`:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "4114d6dc-985b-4ed4-9e5d-543b6d7fdb8f",
  "role": "CUSTOMER"
}
```
Send the token on every request:
```
Authorization: Bearer <access_token>
```
Tokens are HS256-signed JWTs carrying `sub` (user id), `role` and `exp`. They expire after `ACCESS_TOKEN_EXPIRE_MINUTES` (60 by default).

### Access levels
| Level | Who | Used for |
|---|---|---|
| **CUSTOMER** | Users with role `CUSTOMER` who have a customer profile | Every endpoint that reads or changes customer-owned data |
| **Any authenticated** | Any active user with a valid token, of any role | Read-only product catalogues and the biller list |

### Identity and ownership rules
These rules apply to every customer endpoint:

1. **Identity always comes from the JWT**: `JWT → user → customer → resource`. No endpoint accepts a `customer_id` from the client.
2. **Unknown request fields are rejected.** Request bodies use strict schemas, so sending `customer_id` or any other unexpected field returns `422`.
3. **Every customer-owned resource is ownership-checked.** Accounts, transactions, payees, transfers, bill payments, loan applications, investments and recommendations are queried with the caller's `customer_id` in the filter.
4. **Other customers' resources return `404`, not `403`.** An ID that exists but belongs to someone else is indistinguishable from one that doesn't exist, which prevents ID enumeration.

### Authentication and authorization errors
| Status | `detail` | Cause |
|---|---|---|
| `401` | `Authentication required` | No `Authorization` header |
| `401` | `Invalid or expired token` | Malformed, tampered or expired token |
| `401` | `User account is unavailable` | User deleted or deactivated |
| `403` | `Insufficient permissions` | Valid token, but the role is not allowed (for example a RELATIONSHIP_MANAGER calling `/accounts`) |
| `404` | `Customer profile not found` | CUSTOMER role, but no customer profile is linked to the user |

`401` responses include the header `WWW-Authenticate: Bearer`.

---

## 3. Conventions

### Data types
| Type | Format | Example |
|---|---|---|
| IDs | UUID v4 string | `"849a45f2-21e6-4eac-b6e6-e48a8db3b2b1"` |
| Money (response) | Decimal **string** with 2 decimal places | `"150000.00"` |
| Money (request) | JSON number or numeric string, `> 0`, at most 2 decimal places | `5000`, `1500.50`, `"1500.50"` |
| Rates and scores | Decimal string with 4 decimal places | `"10.5000"`, `"0.5875"` |
| Timestamps | ISO-8601, UTC | `"2026-10-04T07:43:12.137680Z"` |
| Dates | ISO-8601 date | `"2026-10-05"` |
| Currency | ISO-4217 code | `"INR"` |

Money is returned as a string so that clients don't lose precision by parsing it as a float. Parse it with a decimal library.

### Masked account numbers
Account numbers are **never returned in full**. Account and payee responses show only the last 4 characters, for example `"XXXX1234"`. Clients identify accounts by their `id`, never by account number. Audit logs store masked numbers too.

### Enumerated filters
Query filters on enumerated values (`category`, `transaction_type`, `loan_type`, `product_type`, `risk_level`, `insurance_type`, and so on) are **case-insensitive**: `groceries` matches `GROCERIES`.

### Pagination
Endpoints that can return large result sets are paginated.

| Query param | Type | Default | Constraints |
|---|---|---|---|
| `page` | int | `1` | ≥ 1 |
| `page_size` | int | `20` | 1–100 (`MAX_PAGE_SIZE`) |

Paginated response envelope:
```json
{
  "items": [ ... ],
  "page": 1,
  "page_size": 20,
  "total": 124
}
```
`total` is the number of matching records across all pages. The paginated endpoints are `/accounts/{id}/transactions`, `/transfers` and `/bills/history`. Other list endpoints return a plain JSON array, or `{items, total}` for `/accounts`, because their result sets are naturally small.

### Error format
**Business-rule and resource errors** have a single message:
```json
{ "detail": "Insufficient available balance" }
```

**Request validation errors** (`422`) use FastAPI's standard list format:
```json
{
  "detail": [
    {
      "type": "extra_forbidden",
      "loc": ["body", "customer_id"],
      "msg": "Extra inputs are not permitted",
      "input": "00000000-0000-0000-0000-000000000000"
    }
  ]
}
```

### Status codes
| Code | Meaning |
|---|---|
| `200 OK` | Successful read or update |
| `201 Created` | Resource created (payee, transfer, bill payment, loan application, investment) |
| `204 No Content` | Successful deactivation (payee delete) |
| `401 Unauthorized` | Missing, invalid or expired token |
| `403 Forbidden` | Authenticated, but the role is not permitted |
| `404 Not Found` | Resource doesn't exist, **or isn't owned by the caller** |
| `409 Conflict` | Duplicate resource, or an invalid state change (for example cancelling a completed transfer) |
| `422 Unprocessable Entity` | Invalid input, or a business rule was violated (insufficient funds, limits, minimums) |

---

## 4. Cross-cutting behaviour

### Transactional integrity
Operations that move money (transfers, bill payments, investment purchases with a debit) run in **a single database transaction**:
- All validation happens before anything is written.
- Affected account rows are locked (`SELECT … FOR UPDATE`) to prevent concurrent double-spending. When two accounts are involved, they are locked in a fixed order to avoid deadlocks.
- The balance update, ledger transaction, business record, audit log and notification are committed together. Any failure leaves the database unchanged.

All arithmetic uses `Decimal`, never floating point.

### Ledger entries
Every money movement creates a row in `transactions` with status `COMPLETED` and channel `ONLINE`:

| Operation | Type | Category | Reference prefix |
|---|---|---|---|
| Transfer: debit of the source account | `DEBIT` | `TRANSFER` | `TXN-` |
| Internal transfer: credit of the destination account | `CREDIT` | `TRANSFER` | `TXN-` |
| Bill payment | `DEBIT` | `BILL_PAYMENT` | `TXN-` |
| Investment purchase paid from an account | `DEBIT` | `INVESTMENT` | `TXN-` |

Business references have the format `<PREFIX>-<YYYYMMDD>-<12 random hex chars>`, for example `TRF-20261004-A10C62371240`. The prefixes are `TRF` (transfers), `BILL` (bill payments) and `TXN` (ledger transactions).

### Audit logging
Every state-changing customer action writes an `audit_logs` row containing `user_id`, `action`, `entity_type`, `entity_id`, `old_value` / `new_value` (JSON, where relevant), the client `ip_address`, the `user_agent` and `created_at`. Account numbers are masked, and no secrets are stored.

| Action | Entity type | Trigger |
|---|---|---|
| `CUSTOMER_PROFILE_UPDATED` | `CUSTOMER` | `PATCH /customers/me` (only when a value actually changes) |
| `PAYEE_CREATED` | `PAYEE` | `POST /payees` |
| `PAYEE_UPDATED` | `PAYEE` | `PATCH /payees/{id}` |
| `PAYEE_DEACTIVATED` | `PAYEE` | `DELETE /payees/{id}` |
| `TRANSFER_CREATED` | `TRANSFER` | `POST /transfers` |
| `TRANSFER_COMPLETED` | `TRANSFER` | Immediate transfer completes |
| `TRANSFER_CANCELLED` | `TRANSFER` | `POST /transfers/{id}/cancel` |
| `BILL_PAYMENT_COMPLETED` | `BILL_PAYMENT` | `POST /bills/pay` |
| `LOAN_APPLICATION_SUBMITTED` | `LOAN_APPLICATION` | `POST /loans/applications` |
| `INVESTMENT_PURCHASED` | `CUSTOMER_INVESTMENT` | `POST /investments` |

### Notifications
Customer-visible events create a row in `notifications` (severity `INFO`) for the customer's user:

| Type | Trigger |
|---|---|
| `TRANSFER_COMPLETED` | Immediate transfer completed |
| `TRANSFER_SCHEDULED` | Scheduled transfer created |
| `TRANSFER_CANCELLED` | Transfer cancelled |
| `BILL_PAYMENT_COMPLETED` | Bill paid |
| `LOAN_APPLICATION_SUBMITTED` | Loan application submitted |
| `INVESTMENT_PURCHASED` | Investment recorded |

### Security events for fraud monitoring
Transfers of **₹2,00,000 or more** write a `security_events` row with type `HIGH_VALUE_TRANSFER` and severity `WARNING`. Its metadata holds the transfer id, the amount and whether the payee is verified. The fraud engine owned by the Internal team can consume these events; the customer module does not score fraud itself.

### Configuration
These limits are set in `app/core/config.py` and can be overridden with environment variables:

| Setting | Env var | Default | Purpose |
|---|---|---|---|
| `max_single_transfer_amount` | `MAX_SINGLE_TRANSFER_AMOUNT` | `500000` | Maximum amount of one transfer (INR) |
| `daily_transfer_limit` | `DAILY_TRANSFER_LIMIT` | `1000000` | Maximum total of a customer's transfers per UTC day (INR) |
| `max_page_size` | `MAX_PAGE_SIZE` | `100` | Upper bound for `page_size` |

The high-value transfer threshold (₹2,00,000) is a constant in `app/services/payment_service.py`.

---

## 5. Mapping to the use case document

| Use case / scope item | Status | API |
|---|---|---|
| **UC-02** View banking dashboard: balance, recent transactions, recommendations | ✅ | `GET /customers/me/summary`, `GET /accounts`, `GET /accounts/{id}/transactions`, `GET /recommendations` |
| **Account Services**: view account details | ✅ | `GET /accounts/{id}` |
| **Account Services**: transaction search | ✅ | `GET /accounts/{id}/transactions` (filters and search) |
| **Account Services**: account settings management | ✅ (profile) | `PATCH /customers/me` |
| **UC-03** Download account statement (PDF) | ⏳ Not yet implemented | — |
| **UC-04** Transfer money: source account, payee, amount, validation (balance, limits) | ✅ | `POST /transfers` |
| **UC-04** Fraud checks on transfers | ◐ Partial | High-value transfers raise a `HIGH_VALUE_TRANSFER` security event; scoring is owned by the Internal team |
| **UC-05** Manage payees: add, edit, delete | ✅ | `POST/GET/PATCH/DELETE /payees` |
| **UC-05** Verify payee | ◐ Partial | `is_verified` is exposed, but there's no verification workflow yet (always `false`) |
| **Payments & Transfers**: bill payments | ✅ | `GET /billers`, `POST /bills/pay`, `GET /bills/history` |
| **Payments & Transfers**: scheduled transfers | ◐ Partial | Can be created, listed and cancelled; nothing executes them at the scheduled time yet |
| **Payments & Transfers**: transaction history | ✅ | `GET /transfers`, `GET /accounts/{id}/transactions` |
| **Loans**: catalogue, eligibility check, EMI calculator, applications, tracking | ✅ | `/loans/*` |
| **UC-06** Loan recommendation | ✅ (exposure) | Eligibility uses income, credit score and existing obligations; recommendations are exposed via `GET /recommendations` |
| **Wealth Management**: fixed deposits, mutual funds, stocks and bonds | ✅ (catalogue + simulated purchase) | `/investments/*` |
| **Wealth Management**: insurance products | ✅ (catalogue) | `/insurance/products` |
| **Wealth Management**: product comparison | ✅ (data) | Catalogue endpoints return comparable attributes; the comparison UI is frontend scope |
| **UC-07 / UC-12** Investment and product recommendations | ✅ (exposure) | `GET /recommendations`; the engine is owned by the Internal team |
| **NFR Security**: secure auth, RBAC, audit logs, OWASP Top 10 | ✅ | See sections 2 and 4 |

---

## 6. Source layout

```
backend/app/
├── api/                      # Routers: auth dependency, validation, HTTP mapping
│   ├── customers.py  accounts.py  transactions.py  payees.py  transfers.py
│   ├── bills.py  loans.py  investments.py  insurance.py  recommendations.py
├── services/                 # Business rules, DB access, transactions
│   ├── common.py                 # ownership helpers, ledger, audit, notifications, pagination
│   ├── customer_service.py  account_service.py  transaction_service.py
│   ├── payee_service.py  payment_service.py (transfers + bills)
│   ├── loan_service.py  investment_service.py  insurance_service.py
│   └── recommendation_service.py
├── schemas/                  # Pydantic request/response contracts
├── core/
│   ├── dependencies.py           # get_current_user, require_roles, get_current_customer, RequestContext
│   └── exceptions.py             # NotFoundError / ConflictError / BusinessRuleError → HTTP mapping
└── models/                   # SQLAlchemy models (schema source of truth)
```

Schema changes made for this module:
- Migration `a3c1f2d4e5b6` adds `payees.is_active` (boolean, default `true`) to support soft deactivation.
