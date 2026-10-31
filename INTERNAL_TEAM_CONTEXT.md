
# PBIP Internal Intelligence Team Context

## 1. Purpose

This document is the implementation contract for the PBIP Internal Intelligence team.

This team owns the internal banking-side intelligence capabilities:

- Fraud detection
- Fraud alerts
- Fraud investigations
- Behavioural analytics
- Customer risk scoring
- Financial health metrics
- Product recommendations
- Compliance dashboards
- Operational analytics
- Internal reporting

The internal side should demonstrate how a bank can turn customer activity into actionable intelligence.

---

# 2. Project Context

PBIP is a Personal Banking Intelligence Platform.

The platform combines customer-facing banking functionality with internal intelligence.

The internal portal is intended for:

- Fraud analysts
- Compliance officers
- Relationship managers
- Administrators

The backend runs as two services (customer-service, admin-service) behind an nginx gateway, sharing one codebase and one database. See `docs/architecture/MICROSERVICES_MIGRATION_PLAN.md`.

Backend:

    FastAPI
    SQLAlchemy 2.x
    PostgreSQL / Supabase
    Alembic

Architecture:

    Router
       ↓
    Schema
       ↓
    Service
       ↓
    SQLAlchemy
       ↓
    PostgreSQL

Do not create further microservices; internal APIs belong in admin-service (`app/admin_main.py`). New router prefixes must also be added to the admin location in `gateway/nginx.conf`.

---

# 3. Existing Roles

The authentication system already supports:

- CUSTOMER
- RELATIONSHIP_MANAGER
- FRAUD_ANALYST
- COMPLIANCE_OFFICER
- ADMIN

Use existing RBAC dependencies.

Do not create a second authorization mechanism.

---

# 4. Internal Team Ownership

The Internal team owns:

## Fraud

- Fraud risk scoring
- Fraud event creation
- Fraud alert generation
- Alert prioritization
- Alert status management
- Investigation workflow

## Behavioural Analytics

- Customer behaviour aggregation
- Spending patterns
- Transaction trends
- Customer segments
- Session/activity analysis
- Behaviour anomalies

## Customer Intelligence

- Customer risk profiles
- Financial health score
- Savings ratio
- Debt-to-income ratio
- Fraud risk score

## Recommendations

- Product recommendation generation
- Recommendation scoring
- Recommendation reasons
- Recommendation lifecycle

## Compliance

- Risk dashboards
- High-risk customer views
- Suspicious activity views
- Audit/security event reporting

---

# 5. Existing Database Tables

Relevant intelligence tables:

```text
behaviour_events
customer_risk_profiles
recommendations
fraud_events
fraud_alerts
fraud_investigations
notifications
audit_logs
security_events
```

Existing customer/banking tables provide source data:

```text
customers
accounts
transactions
payees
transfers
bill_payments
loan_products
loan_applications
investment_products
customer_investments
insurance_products
```

## 6. Synthetic Data Is Mandatory

The intelligence layer requires enough data to produce meaningful analytics.

The project should not depend only on manually created demo records.

Use synthetic data generators to create realistic:

- Customers
- Accounts
- Transactions
- Behaviour events
- Fraud events
- Product interactions

Data should have realistic distributions.

Avoid generating completely random independent values.

For example:

A customer's transactions should correlate with:

- Income
- Customer segment
- Account balance
- Spending patterns
- Occupation
- Risk profile

## 7. Synthetic Data Pipeline

Recommended structure:

```text
data/
├── generators/
│   ├── config.py
│   ├── customer_generator.py
│   ├── transaction_generator.py
│   ├── behaviour_generator.py
│   ├── fraud_generator.py
│   └── generate.py
│
└── seeds/
```

The generator should support deterministic seeds where practical.

Example:

`python -m data.generators.generate`

The generated dataset should be reproducible.

## 8. Behavioural Analytics

The behavioural system should convert raw activity into useful customer-level insights.

Examples:

- Monthly spending
- Category distribution
- Transaction frequency
- Average transaction amount
- Income vs spending
- Savings ratio
- Weekend vs weekday spending
- Digital channel usage
- Product engagement
- Login/session behaviour
## 9. Financial Health Metrics

For each customer calculate useful metrics.

Examples:

**Savings ratio**

```text
Savings Ratio =
(Income - Spending) / Income
```

Handle zero-income cases safely.

**Debt-to-income ratio**

```text
DTI =
Monthly Debt Obligations / Monthly Income
```

The exact implementation can use available project data.

Financial Health Score

Create a normalized score based on measurable signals such as:

- Savings ratio
- DTI
- Account balance stability
- Spending volatility
- Transaction behaviour

Keep the scoring transparent.

The project should be able to explain why a customer received a particular score.

## 10. Customer Segmentation

Create meaningful customer segments.

Potential segments:

- `MASS_MARKET`
- `MASS_AFFLUENT`
- `AFFLUENT`
- `HIGH_NET_WORTH`

The actual segmentation logic should be documented.

Possible inputs:

- Income
- Balance
- Investment holdings
- Spending
- Product usage

Do not create arbitrary random segments.

## 11. Behavioural API

### GET `/api/v1/analytics/customers/{customer_id}`

Return customer analytics.

Possible response:

```json
{
  "customer_id": "uuid",
  "financial_health_score": 78.4,
  "savings_ratio": 0.24,
  "debt_to_income_ratio": 0.31,
  "monthly_income": 100000,
  "monthly_spending": 76000,
  "transaction_count": 42,
  "top_spending_categories": [],
  "risk_profile": "MODERATE"
}
```

Access:

- `RELATIONSHIP_MANAGER`
- `ADMIN`

Customer-facing analytics should be exposed separately if required.

## 12. Analytics Overview

### GET `/api/v1/analytics/overview`

This is a primary internal dashboard endpoint.

Return aggregated platform metrics.

Example response:

```json
{
  "total_customers": 1000,
  "active_customers": 742,
  "total_accounts": 1280,
  "total_transactions": 45231,
  "total_transaction_value": 125000000,
  "fraud_alerts": 37,
  "high_risk_customers": 52,
  "loan_applications": 148,
  "investment_value": 25000000
}
```

Use real database values.

Do not hardcode dashboard numbers.

## 13. Transaction Trends

### GET `/api/v1/analytics/transactions/trends`

Support a period filter.

Example:

`?period=30d`

Return:

- Date
- Transaction count
- Transaction value

Example response:

```json
[
  {
    "date": "2026-09-01",
    "transaction_count": 1520,
    "transaction_value": 4200000
  }
]
```

## 14. Spending Categories

### GET `/api/v1/analytics/spending/categories`

Return aggregated spending by category.

Example response:

```json
[
  {
    "category": "FOOD",
    "amount": 125000,
    "percentage": 18.4
  },
  {
    "category": "TRAVEL",
    "amount": 85000,
    "percentage": 12.5
  }
]
```

## 15. Customer Segments

### GET `/api/v1/analytics/customers/segments`

Return customer counts by segment.

Example response:

```json
[
  {
    "segment": "MASS_MARKET",
    "count": 620
  },
  {
    "segment": "MASS_AFFLUENT",
    "count": 280
  }
]
```

## 16. Fraud Detection

Fraud detection is one of the major differentiating capabilities of PBIP.

The objective is not to build a production bank fraud engine.

The objective is to demonstrate a realistic multi-signal fraud monitoring pipeline.

## 17. Fraud Signals

Potential fraud signals:

- Unusually high transaction amount
- Transaction velocity
- Sudden geographic change
- Unusual merchant category
- New device
- New location
- Multiple failed transactions
- Unusual transaction timing
- Sudden account activity spike
- Transaction inconsistent with historical behaviour

Use multiple signals rather than one rule.

## 18. Fraud Risk Score

Generate a score between:

`0` and `100`

Suggested interpretation:

- `0–29`: LOW
- `30–59`: MEDIUM
- `60–79`: HIGH
- `80–100`: CRITICAL

The score must be explainable.

Example:

```json
{
  "risk_score": 87,
  "severity": "CRITICAL",
  "reasons": [
    "Transaction amount significantly exceeds customer baseline",
    "Unusual geographic location",
    "High transaction velocity"
  ]
}
```

These thresholds are implementation guidance and should be kept configurable where practical.

## 19. Fraud Event

When suspicious activity is detected, create:

`fraud_events`

Fields include:

- `customer_id`
- `transaction_id`
- `event_type`
- `risk_score`
- `severity`
- `description`
- `metadata`
- `detected_at`

Do not overwrite the original transaction.

## 20. Fraud Alert

Create:

`fraud_alerts`

An alert represents an actionable case for an analyst.

Possible statuses:

- `OPEN`
- `IN_REVIEW`
- `ESCALATED`
- `RESOLVED`
- `FALSE_POSITIVE`

Priority:

- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

## 21. Fraud APIs

### GET `/api/v1/fraud/alerts`

Accessible to:

- `FRAUD_ANALYST`
- `ADMIN`

Support:

- `status`
- `severity`
- `priority`
- Date range
- Customer
- Pagination

### GET `/api/v1/fraud/alerts/{alert_id}`

Return alert details.

### PATCH `/api/v1/fraud/alerts/{alert_id}`

Update:

- `status`
- `priority`
- Assigned analyst
- Resolution notes

Only appropriate roles may modify alerts.

## 22. Fraud Investigation

### POST `/api/v1/fraud/alerts/{alert_id}/investigations`

Create investigation.

Store:

- `alert_id`
- `analyst_id`
- `notes`
- `action_taken`
- `started_at`

### PATCH `/api/v1/fraud/investigations/{investigation_id}`

Update investigation.

When completed:

- Set `completed_at`
- Update alert status
- Store resolution notes

## 23. Fraud Dashboard

The fraud dashboard should answer:

- How many alerts exist?
- How many are critical?
- Which customers are high risk?
- Which transaction types generate alerts?
- What is the alert trend?
- How many alerts are unresolved?
- What actions have analysts taken?

Useful metrics:

- Total alerts
- Open alerts
- Critical alerts
- Resolved alerts
- False positives
- Average risk score
- Alerts by type
- Alerts by severity
- Alerts over time

## 24. Recommendations

Recommendations should use customer data.

Examples:

**Example customer profile:**

A customer with:

- High savings
- Moderate risk tolerance
- Low investment exposure

may receive an investment recommendation.

A customer with:

- Stable income
- Good financial health
- Eligible loan profile

may receive a loan recommendation.

The recommendation must contain a reason.

**Bad:**

> Recommended because score = 87.

**Better:**

> Recommended because your monthly savings have remained stable and your current investment allocation is low relative to your financial profile.

## 25. Recommendation API

### GET `/api/v1/recommendations`

Customer-facing endpoint.

The Internal team owns generation.

Internal generation

A service such as:

`recommendation_service.py`

should:

- Retrieve customer profile
- Retrieve behavioural metrics
- Retrieve risk profile
- Retrieve available products
- Calculate recommendation score
- Generate reason
- Store recommendation

## 26. Recommendation Lifecycle

Statuses:

- `ACTIVE`
- `VIEWED`
- `ACCEPTED`
- `DISMISSED`
- `EXPIRED`

Recommendations should have:

- `created_at`
- `expires_at`

Avoid generating duplicate active recommendations unnecessarily.

## 27. Risk Profile

Table:

`customer_risk_profiles`

Track:

- `risk_tolerance`
- `credit_score`
- `fraud_risk_score`
- `financial_health_score`
- `savings_ratio`
- `debt_to_income_ratio`
- `last_calculated_at`

The profile should be recalculated when meaningful underlying data changes or during scheduled analytics generation.

## 28. Compliance APIs

Compliance users should be able to inspect risk-oriented information.

### GET `/api/v1/compliance/risk-summary`

Return:

- High-risk customers
- Fraud risk distribution
- Suspicious activity counts
- Unresolved alerts
- High-risk transactions

Access:

- `COMPLIANCE_OFFICER`
- `ADMIN`
## 29. Security Events

Use:

`security_events`

Examples:

- `LOGIN_SUCCESS`
- `LOGIN_FAILURE`
- `SUSPICIOUS_LOGIN`
- `PASSWORD_CHANGE`
- `TOKEN_FAILURE`
- `ACCOUNT_LOCKED`
- `UNUSUAL_DEVICE`

Security events should support internal investigation.

## 30. Audit Logs

Audit logs are not the same as fraud events.

**Audit log**

Answers:

- Who performed what action?

**Fraud event**

Answers:

- What suspicious behaviour was detected?

Do not merge the two concepts.

## 31. Data Refresh Strategy

For the project, intelligence can be calculated through:

- On-demand API calculation
- Seed-time calculation
- Explicit analytics generation script
- Background jobs if added later

Do not introduce Celery/Kafka/etc. unless necessary.

A simple service-based approach is sufficient.

## 32. Testing

**Fraud tests:**

- Low-risk transaction
- High-value transaction
- Velocity anomaly
- Geographic anomaly
- Multiple signals
- Alert creation
- Alert status transition
- Role authorization

**Analytics tests:**

- Spending aggregation
- Transaction trends
- Financial health calculation
- Savings ratio
- DTI
- Segmentation

**Recommendation tests:**

- Product matching
- Recommendation score
- Recommendation reason
- Duplicate prevention
- Expiry

**RBAC tests:**

- Customer → `403`
- Relationship Manager → allowed where applicable
- Fraud Analyst → fraud endpoints
- Compliance Officer → compliance endpoints
- Admin → internal endpoints
## 33. Performance

Analytics endpoints should avoid fetching every transaction into Python unnecessarily.

Prefer database aggregation:

- `COUNT()`
- `SUM()`
- `AVG()`
- `GROUP BY`
- `DATE_TRUNC()`

Use indexes on commonly filtered columns.

Potential indexes:

- `transactions.account_id`
- `transactions.transaction_date`
- `transactions.category`
- `transactions.is_fraud`
- `fraud_alerts.status`
- `fraud_alerts.severity`
- `fraud_alerts.created_at`
- `behaviour_events.customer_id`
- `behaviour_events.timestamp`

## 34. Out of Scope

Do NOT build:

- Production ML fraud model
- Real-time Kafka pipeline
- Real bank fraud provider
- Real AML submission system
- Real regulatory reporting integration
- Production credit bureau integration
- Complex distributed analytics infrastructure

The goal is a convincing, explainable intelligence platform.

## 35. Definition of Done

A feature is complete when:

- Database changes are migrated
- Service logic exists
- API exists
- RBAC exists
- Business logic is tested
- Aggregations are validated
- Dashboard data is dynamic
- No hardcoded analytics
- API documented in Swagger
- Relevant audit/security events exist
- Context documentation updated
## 36. Core Principle

The internal portal should answer one question:

"What is happening across the bank, and what requires attention?"

The dashboard should therefore prioritize:

- Risk
- Trends
- Exceptions
- Customer behaviour
- Fraud
- Recommendations
- Actionable cases

Do not build a dashboard that is merely a collection of decorative charts.
