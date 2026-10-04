# PBIP Customer Team Context

## 1. Purpose

This document is the implementation contract for the PBIP Customer Banking team.

The Customer team owns the customer-facing banking capabilities exposed through the FastAPI backend.

The goal is to provide a realistic, secure, API-first banking experience covering:

- Customer profile
- Accounts
- Account balances
- Transaction history
- Transaction search/filtering
- Payee management
- Transfers
- Scheduled transfers
- Billers
- Bill payments
- Loan catalogue
- Loan eligibility
- Loan applications
- Investment products
- Customer investments
- Insurance products

The team is responsible for backend business logic and APIs.

The frontend is owned by the Frontend/AI team and consumes these APIs.

---

# 2. Project Context

PBIP is a Personal Banking Intelligence Platform designed as an industry-aligned banking technology solution.

The overall system combines:

1. Traditional banking functionality
2. Financial analytics
3. Behavioural intelligence
4. Fraud detection
5. Product recommendations
6. AI-assisted banking interactions
7. Internal banking operations

The architecture is a modular monolith.

The backend follows:

Router → Pydantic Schema → Service → SQLAlchemy → PostgreSQL

Do NOT introduce microservices for individual banking features.

---

# 3. Existing Foundation

The following functionality is already implemented and should be treated as existing infrastructure.

## Authentication

Implemented:

- User registration
- User login
- JWT access tokens
- Password hashing using bcrypt
- `/api/v1/auth/register`
- `/api/v1/auth/login`
- `/api/v1/me`
- Role-based access control
- `get_current_user()`
- `require_roles()`
- Login security events
- Authentication audit logs

Supported roles:

- CUSTOMER
- RELATIONSHIP_MANAGER
- FRAUD_ANALYST
- COMPLIANCE_OFFICER
- ADMIN

Do NOT rebuild authentication.

Use the existing authentication dependencies.

---

# 4. Existing Database Foundation

The project uses:

- PostgreSQL
- Supabase
- SQLAlchemy 2.x
- asyncpg
- Alembic

Existing identity tables:

- users
- customers

Relevant banking tables:

- accounts
- transactions
- payees
- transfers
- billers
- bill_payments

Product tables:

- loan_products
- loan_applications
- investment_products
- customer_investments
- insurance_products

Intelligence tables:

- customer_risk_profiles
- recommendations

AI and internal teams use the same database but must access customer functionality through services/APIs rather than duplicating business logic.

---

# 5. Customer Team Ownership

The Customer team owns:

## Customer

- Customer profile retrieval
- Customer profile updates where allowed
- Customer financial summary

## Accounts

- Account listing
- Account details
- Balance information
- Available balance
- Account status
- Account transaction history

## Transactions

- Transaction listing
- Transaction details
- Filtering
- Search
- Date ranges
- Categories
- Transaction types
- Pagination

## Payees

- Add payee
- List payees
- Update payee
- Delete/deactivate payee
- Payee verification state

## Transfers

- Internal transfer
- Payee transfer
- Scheduled transfer
- Transfer status
- Transfer history

## Bills

- Biller catalogue
- Bill payment
- Bill payment history
- Due dates
- Payment status

## Loans

- Loan product catalogue
- Loan eligibility
- EMI calculation
- Loan application
- Application tracking

## Investments

- Investment product catalogue
- Product details
- Customer investment holdings
- Investment purchase simulation/record

## Insurance

- Insurance product catalogue
- Product details

---

# 6. API Prefix

All APIs must be exposed below:

    /api/v1

Use REST-style resource naming.

Example:

    GET /api/v1/accounts
    GET /api/v1/accounts/{account_id}
    GET /api/v1/accounts/{account_id}/transactions

---

# 7. Customer APIs

## 7.1 Customer Profile

### GET /api/v1/customers/me

Returns the authenticated customer's profile.

Example response:

```json
{
  "id": "uuid",
  "customer_number": "CUST000001",
  "first_name": "Atharva",
  "last_name": "Deokar",
  "email": "customer@pbip.demo",
  "phone": "+91XXXXXXXXXX",
  "city": "Mumbai",
  "state": "Maharashtra",
  "occupation": "Software Engineer",
  "employment_type": "SALARIED",
  "annual_income": 1200000,
  "risk_profile": "MODERATE",
  "customer_segment": "MASS_AFFLUENT"
}
```

The email should come from the authenticated user.

Never allow a customer to retrieve another customer's profile through a customer-facing endpoint.

## 8. Account APIs

### GET `/api/v1/accounts`

Return all accounts belonging to the authenticated customer.

Example response:

```json
{
  "items": [
    {
      "id": "uuid",
      "account_number": "XXXX1234",
      "account_type": "SAVINGS",
      "currency": "INR",
      "balance": 125000.50,
      "available_balance": 120000.50,
      "status": "ACTIVE"
    }
  ],
  "total": 1
}
```

### GET `/api/v1/accounts/{account_id}`

Return account details.

**Security requirement:**

The authenticated customer must own the account.

Never trust an account_id supplied by the frontend without ownership validation.

## 9. Transaction APIs

### GET `/api/v1/accounts/{account_id}/transactions`

Supported query parameters:

- `page`
- `page_size`
- `category`
- `transaction_type`
- `transaction_status`
- `start_date`
- `end_date`
- `min_amount`
- `max_amount`
- `search`

Example:

`GET /api/v1/accounts/{id}/transactions?page=1&page_size=20`

Return paginated results.

Example response:

```json
{
  "items": [],
  "page": 1,
  "page_size": 20,
  "total": 124
}
```

### GET `/api/v1/transactions/{transaction_id}`

Return transaction details.

Validate ownership through the related account.

## 10. Payee APIs

### POST `/api/v1/payees`

Create a payee.

Required fields:

- `name`
- `account_number`
- `bank_name`
- `IFSC`
- `nickname`

Initial implementation may use:

`is_verified = false`

unless the project implements a verification workflow.

### GET `/api/v1/payees`

Return customer's payees.

### PATCH `/api/v1/payees/{payee_id}`

Update editable payee information.

### DELETE `/api/v1/payees/{payee_id}`

Prefer deactivation over physical deletion if practical.

## 11. Transfer APIs

Transfers are a major customer journey.

### POST `/api/v1/transfers`

Request:

```json
{
  "source_account_id": "uuid",
  "payee_id": "uuid",
  "amount": 5000,
  "transfer_type": "IMMEDIATE"
}
```

For scheduled transfers:

```json
{
  "source_account_id": "uuid",
  "payee_id": "uuid",
  "amount": 5000,
  "transfer_type": "SCHEDULED",
  "scheduled_at": "2026-10-01T10:00:00"
}
```

**Validation**

Before creating a transfer:

- Authenticate user.
- Verify source account ownership.
- Verify source account is active.
- Verify payee belongs to customer.
- Validate amount > 0.
- Validate sufficient available balance.
- Validate transfer type.
- Validate scheduled date where applicable.
- Generate unique reference number.
- Create transfer record.
- Update relevant balance/transaction state.
- Write audit log.
- Generate notification where appropriate.

The operation should be transactional.

Do not partially update the database.

## 12. Transfer States

Recommended states:

- `PENDING`
- `PROCESSING`
- `COMPLETED`
- `FAILED`
- `CANCELLED`
- `SCHEDULED`

The implementation should keep state transitions explicit.

Do not allow arbitrary status changes from the frontend.

## 13. Bill APIs

### GET `/api/v1/billers`

Return active billers.

Optional filters:

- `category`
- `provider_code`

### POST `/api/v1/bills/pay`

Request:

```json
{
  "account_id": "uuid",
  "biller_id": "uuid",
  "amount": 1500,
  "due_date": "2026-10-05"
}
```

**Validation:**

- Account ownership
- Account status
- Sufficient balance
- Biller active
- Amount > 0

Create a bill payment record.

Generate a payment reference.

Create an audit entry.

### GET `/api/v1/bills/history`

Return the customer's bill payment history.

## 14. Loan APIs

### GET `/api/v1/loans/products`

Return active loan products.

Example response:

```json
{
  "id": "uuid",
  "name": "Personal Loan",
  "loan_type": "PERSONAL",
  "min_amount": 50000,
  "max_amount": 2000000,
  "interest_rate": 10.5,
  "min_tenure_months": 12,
  "max_tenure_months": 60,
  "description": "..."
}
```

### POST `/api/v1/loans/eligibility`

Input:

```json
{
  "loan_product_id": "uuid",
  "requested_amount": 500000,
  "tenure_months": 36
}
```

The service should calculate:

- Eligibility
- Indicative EMI
- Eligibility score
- Basic reasons

The implementation may use customer data such as:

- Annual income
- Credit score
- Existing debt
- Existing accounts
- Risk profile

Do not expose sensitive internal scoring implementation unnecessarily.

### POST `/api/v1/loans/applications`

Create a loan application.

Input:

```json
{
  "loan_product_id": "uuid",
  "requested_amount": 500000,
  "tenure_months": 36
}
```

Persist:

- Customer
- Product
- Amount
- Tenure
- Interest rate
- EMI
- Eligibility score
- Application status
- Application date

Initial status:

`SUBMITTED`

Possible statuses:

- `SUBMITTED`
- `UNDER_REVIEW`
- `APPROVED`
- `REJECTED`
- `CANCELLED`

### GET `/api/v1/loans/applications`

Return the customer's applications.

## 15. EMI Calculation

Use standard reducing-balance EMI:

```text
EMI = P × r × (1+r)^n / ((1+r)^n - 1)
```

Where:

- `P` = principal
- `r` = monthly interest rate
- `n` = number of months

Handle zero-interest cases separately.

This calculation should be unit tested.

## 16. Investment APIs

### GET `/api/v1/investments/products`

Return active investment products.

Filters:

- `product_type`
- `risk_level`

### GET `/api/v1/investments`

Return customer's investment holdings.

### POST `/api/v1/investments`

For the initial project, this may represent a simulated investment purchase.

Request:

```json
{
  "investment_product_id": "uuid",
  "amount_invested": 25000
}
```

Validate:

- Product exists
- Product active
- Minimum investment
- Customer ownership
- Valid amount

Create customer_investments.

## 17. Insurance APIs

### GET `/api/v1/insurance/products`

Return active insurance products.

Filters:

- `insurance_type`
- `risk_level`

Initial scope is catalogue/read-only.

Do NOT implement a full insurance underwriting workflow unless explicitly required later.

## 18. Recommendations

Recommendations are primarily owned by the Internal/Analytics team.

The Customer team only needs to expose them.

### GET `/api/v1/recommendations`

Return recommendations for the authenticated customer.

Possible product types:

- `LOAN`
- `INVESTMENT`
- `INSURANCE`
- `SAVINGS`
- `CREDIT`

Return:

- Product
- Recommendation type
- Score
- Reason
- Status
- `created_at`
- `expires_at`

Do not independently implement recommendation algorithms in the customer module.

## 19. Authorization Rules

Customer APIs must always derive the customer identity from the authenticated JWT.

Never accept:

`customer_id`

from the frontend as the authority for customer-owned resources.

**Correct:**

`JWT → user_id → customer → resource ownership`

**Incorrect:**

`frontend customer_id → query database`

Every customer-owned resource must have an ownership check.

## 20. Audit Requirements

The following actions should create audit logs:

- Payee creation
- Payee update
- Payee deletion/deactivation
- Transfer creation
- Transfer completion/failure
- Bill payment
- Loan application
- Investment purchase
- Important profile changes

Audit logs should capture:

- `user_id`
- `action`
- `entity_type`
- `entity_id`
- `old_value` where appropriate
- `new_value` where appropriate
- IP address when available
- `timestamp`

Do not store plaintext passwords or secrets in audit logs.

## 21. Notifications

Relevant customer events should create notifications.

Examples:

- Transfer completed
- Transfer failed
- Bill payment completed
- Loan application submitted
- Loan approved/rejected
- Suspicious transaction detected
- Recommendation generated

Use the existing notifications table.

## 22. Service Layer

Do not put business logic directly in routers.

Recommended structure:

```text
backend/app/
├── api/
│   ├── customers.py
│   ├── accounts.py
│   ├── transactions.py
│   ├── payees.py
│   ├── transfers.py
│   ├── bills.py
│   ├── loans.py
│   ├── investments.py
│   └── insurance.py
│
├── services/
│   ├── customer_service.py
│   ├── account_service.py
│   ├── transaction_service.py
│   ├── payment_service.py
│   ├── loan_service.py
│   └── investment_service.py
│
└── schemas/
    ├── customer.py
    ├── account.py
    ├── transaction.py
    ├── payee.py
    ├── transfer.py
    ├── bill.py
    ├── loan.py
    ├── investment.py
    └── insurance.py
```

**Router responsibilities:**

- Authentication
- Input validation
- Calling service
- HTTP response

**Service responsibilities:**

- Business rules
- Database operations
- Transactions
- Domain logic

## 23. Testing Requirements

Every major feature must have tests.

Minimum:

- **Unit tests**
  - EMI calculation
  - Transfer validation
  - Insufficient balance
  - Ownership validation
  - Loan eligibility
  - Investment minimum amount
  - Payee ownership
- **API tests**
  - Successful account retrieval
  - Unauthorized access
  - Cross-customer access rejection
  - Transfer creation
  - Invalid transfer
  - Bill payment
  - Loan application
  - Investment creation
- **Security tests**

At minimum verify:

- Customer cannot access another customer's account
- Customer cannot access another customer's transactions
- Customer cannot modify another customer's payee
- Customer cannot perform transfers from another customer's account
- Unauthenticated requests receive `401`
- Incorrect role receives `403`

Target project-wide coverage:

`>= 70%`

## 24. Out of Scope

Do NOT implement unless explicitly requested:

- Real bank payment gateway integration
- Real NPCI/UPI integration
- Real KYC provider
- Real credit bureau
- Production-grade payment settlement
- Actual stock exchange integration
- Actual insurance underwriting
- Microservices
- Event-driven Kafka infrastructure
- Complex distributed transaction systems

This is an industry-aligned academic project using synthetic/demo data.

## 25. Definition of Done

A customer feature is complete only when:

- Database model exists if required
- Alembic migration exists
- Pydantic schemas exist
- Service layer exists
- API route exists
- Authentication is enforced
- Ownership checks exist
- Error handling exists
- Audit logging is implemented where required
- Notifications are implemented where required
- Unit tests exist
- API tests exist
- API appears in Swagger
- README/context documentation is updated if the contract changed
## 26. Dependencies on Other Teams

The Customer team depends on:

- **Internal Team**
  - Recommendations
  - Customer risk profile
  - Behavioural analytics
  - Fraud results
  - Fraud alerts
- **Frontend/AI Team**
  - Frontend integration
  - AI assistant
  - AI tool orchestration

The Customer team must expose stable APIs and should not depend on frontend implementation details.

## 27. Core Principle

Build a believable banking backend, not a collection of disconnected CRUD endpoints.

A customer should be able to:

- Log in
- See accounts
- View transactions
- Add payees
- Transfer money
- Pay bills
- Explore loans
- Check eligibility
- Apply for a loan
- Explore investments
- View recommendations
- Interact with the AI assistant

The entire journey should work using the same customer identity and database state.
## 28. Implementation Notes (contract deltas)

Full API reference: [`docs/api/customer/`](docs/api/customer/README.md).

Implemented in `backend/app/{api,services,schemas}`. Differences from / additions to the contract above:

- **Account numbers are masked** (`XXXX1234`) in all account and payee responses and in audit logs.
- **Customer:** `PATCH /customers/me` (only phone, address, city, state, postal_code, occupation are editable) and `GET /customers/me/summary` (financial summary).
- **Transactions:** listing is account-scoped only (`GET /accounts/{id}/transactions`); `page_size` max is 100.
- **Payees:** new `is_active` column (migration `a3c1f2d4e5b6`). `DELETE /payees/{id}` soft-deactivates and returns `204`. Only `name`, `bank_name`, `nickname` are editable; bank details require a new payee. Request field is `ifsc_code`.
- **Transfers:**
  - Supply exactly one of `payee_id` or `destination_account_id` (own-account internal transfer).
  - Optional `remarks`.
  - Limits: 500,000 per transfer and 1,000,000 per day (configurable in `Settings`).
  - IMMEDIATE transfers complete synchronously (`PENDING → PROCESSING → COMPLETED`).
  - SCHEDULED transfers are stored as `SCHEDULED` with no funds moved; an execution job is not yet implemented.
  - New `GET /transfers/{id}` and `POST /transfers/{id}/cancel` (only `PENDING`/`SCHEDULED`).
  - Transfers ≥ 200,000 write a `HIGH_VALUE_TRANSFER` security event for the fraud engine.
- **Bills:** payment completes synchronously (status `COMPLETED`) and records a `BILL_PAYMENT` debit transaction.
- **Loans:**
  - The eligibility response is `{loan_product_id, eligible, eligibility_score, interest_rate, estimated_emi, reasons: [..]}`.
  - Applications outside product amount/tenure limits are rejected with `422`; a duplicate open application for the same product returns `409`.
  - New `GET /loans/products/{id}` and `GET /loans/applications/{id}`.
- **Investments:** optional `source_account_id` on `POST /investments` debits that account. New `GET /investments/products/{id}`.
- **Insurance:** `GET /insurance/products/{id}` added.
- **Access:**
  - Catalogue endpoints (billers and loan/investment/insurance products) need any authenticated user.
  - All customer-owned endpoints need the `CUSTOMER` role.
  - Another customer's resources return `404`.
