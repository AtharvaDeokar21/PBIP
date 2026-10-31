
# PBIP Frontend + AI Team Context

## 1. Purpose

This document is the implementation contract for the PBIP Frontend + AI team.

This team owns:

1. Customer-facing frontend
2. Internal banking portal frontend
3. Shared UI architecture
4. API integration
5. AI banking assistant
6. AI conversation interface
7. AI tool orchestration
8. Frontend authentication/session handling

The team does NOT own core banking business logic.

---

# 2. Project Context

PBIP is a Personal Banking Intelligence Platform.

The system has two major interfaces:

## Customer Portal

Used by:

- Customers

Capabilities include:

- Dashboard
- Accounts
- Transactions
- Transfers
- Bills
- Loans
- Investments
- Insurance
- Recommendations
- AI assistant
- Notifications
- Profile

## Internal Portal

Used by:

- Relationship Managers
- Fraud Analysts
- Compliance Officers
- Administrators

Capabilities include:

- Analytics
- Customer insights
- Fraud monitoring
- Fraud alerts
- Investigations
- Risk dashboards
- Compliance information

---

# 3. Frontend Architecture

Recommended:

- Next.js
- TypeScript where practical
- Tailwind CSS
- Component-based architecture
- API-driven state
- Responsive layouts

The frontend must not directly access PostgreSQL or Supabase tables.

Correct:

```text
Frontend
   ↓
FastAPI
   ↓
Service Layer
   ↓
PostgreSQL
```

Incorrect:

```text
Frontend
   ↓
Supabase tables directly
```

## 4. Backend API Base URL

Development (API gateway):

`http://localhost:8080/api/v1`

Production URL should be configurable through environment variables.

Example:

`NEXT_PUBLIC_API_URL`

Never hardcode production URLs inside components.

## 5. Authentication

The backend already implements:

- Registration
- Login
- JWT
- `/api/v1/me`
- RBAC

Frontend responsibilities:

- Login form
- Registration form
- Store authentication state securely
- Attach access token to API requests
- Retrieve current user
- Redirect based on role
- Handle `401`
- Handle `403`
- Logout

Do not implement password hashing or authentication rules in the frontend.

## 6. Role-Based Navigation

### `CUSTOMER`

Customer portal:

- Dashboard
- Accounts
- Transactions
- Transfers
- Pay Bills
- Loans
- Investments
- Insurance
- Recommendations
- AI Assistant
- Notifications
- Profile

### `RELATIONSHIP_MANAGER`

Internal portal:

- Overview
- Customers
- Customer Analytics
- Recommendations
- Risk

### `FRAUD_ANALYST`

Internal portal:

- Fraud Dashboard
- Alerts
- Investigations
- Risk

### `COMPLIANCE_OFFICER`

Internal portal:

- Compliance Dashboard
- Risk
- Security Events
- Audit

### `ADMIN`

Admin should have access to the internal operational views appropriate to the role.

Do not expose frontend navigation as the only authorization mechanism.

Backend RBAC remains authoritative.

## 7. Customer Dashboard

The dashboard should provide a useful financial snapshot.

Recommended sections:

- Header
- Greeting
- Customer name
- Notifications
- Profile
- Financial summary
- Total balance
- Available balance
- Number of accounts
- Monthly spending
- Savings ratio
- Accounts

Cards showing:

- Account type
- Masked account number
- Balance
- Currency
Recent Transactions

Show recent transactions with:

- Merchant
- Category
- Amount
- Date
- Status
Recommendations

Show relevant:

- Loan recommendation
- Investment recommendation
- Savings recommendation
AI Assistant

Prominent access to the banking assistant.

## 8. Accounts UI

Account page should provide:

- Account cards
- Balance
- Available balance
- Account status
- Recent transactions
- Transaction search
- Filters
- Date range
- Pagination

Transaction details should be accessible without exposing internal database IDs unnecessarily.

## 9. Transfers UI

Transfer flow:

```text
Select Source Account
        ↓
Select Payee
        ↓
Enter Amount
        ↓
Review
        ↓
Confirm
        ↓
Success / Failure
```

Before submission display:

- Source account
- Payee
- Amount
- Transfer type
- Scheduled date if applicable

Handle backend errors gracefully.

Example:

Insufficient available balance.

Do not display raw backend stack traces.

## 10. Bills UI

Provide:

- Biller catalogue
- Biller categories
- Payment form
- Amount
- Account selection
- Payment confirmation
- Payment history
- Status
## 11. Loans UI

Loan page:

```text
Loan Products
      ↓
Product Details
      ↓
Eligibility Calculator
      ↓
EMI Preview
      ↓
Apply
      ↓
Application Tracking
```

Show:

- Interest rate
- Minimum amount
- Maximum amount
- Tenure
- Indicative EMI
- Eligibility result

The backend remains the authority for eligibility.

Do not calculate final eligibility exclusively in frontend JavaScript.

## 12. Investment UI

Show:

- Investment products
- Product type
- Risk level
- Expected return
- Minimum investment
- Lock-in period
- Current holdings

Product filtering:

- Risk level
- Product type

Investment purchase may initially be simulated.

Clearly communicate simulated/demo behaviour where appropriate.

## 13. Recommendations UI

Recommendation cards should include:

- Product
- Recommendation type
- Reason
- Score if appropriate
- Action

Example:

> Consider: Balanced Investment Fund

Why this is relevant:
Your savings pattern is stable and your current investment
allocation is relatively low.

Avoid presenting recommendation scores as guarantees.

## 14. Internal Dashboard

The internal portal is a major part of the project.

It should feel like an operational banking console rather than a customer dashboard with different colors.

## 15. Internal Overview

Show:

- **KPIs**
  - Total customers
  - Active customers
  - Total accounts
  - Transaction volume
  - Transaction value
  - Open fraud alerts
  - High-risk customers
  - Loan applications
  - Investment value
- **Charts**
  - Transaction trends
  - Customer segments
  - Spending categories
  - Fraud alerts over time
  - Risk distribution
- **Attention queue**

Highlight:

- Critical fraud alerts
- High-risk customers
- Unresolved investigations
- Significant anomalies

## 16. Fraud Dashboard

Fraud analysts should see:

- Alert count
- Critical alerts
- High-priority alerts
- Open alerts
- Resolved alerts
- False positives
- Alert trend

**Table columns:**

- Alert ID
- Customer
- Transaction
- Risk score
- Severity
- Priority
- Status
- Detected at
- Assigned analyst

Allow filtering.

## 17. Fraud Alert Detail

Detail view:

- Customer
- Transaction
- Risk score
- Severity
- Reasons
- Metadata
- Detection timestamp
- Current status
- Assigned analyst
- Investigation notes
- Actions

Analyst actions:

- Assign
- Mark in review
- Escalate
- Resolve
- Mark false positive

Every action should call the backend API.

## 18. Compliance Dashboard

Show:

- High-risk customers
- Suspicious activity
- Fraud risk distribution
- Security events
- Unresolved alerts
- Audit activity

Do not expose information to roles that the backend does not authorize.

## 19. AI Assistant

The AI assistant is a core differentiator of PBIP.

The assistant should support natural-language banking queries.

Examples:

- How much did I spend this month?
- Show my largest transactions this month.
- How much money do I have across my accounts?
- Which loan am I eligible for?
- Why was this loan recommended?
- Show my recent transactions.
- What are my current investments?
- Help me understand my spending.

## 20. AI Architecture

The AI must NOT directly query PostgreSQL.

Correct architecture:

```text
User
  ↓
Frontend Chat
  ↓
FastAPI / AI Endpoint
  ↓
AI Service
  ↓
Groq LLM
  ↓
Tool Selection
  ↓
Backend Business APIs / Services
  ↓
PostgreSQL
  ↓
Tool Result
  ↓
Groq
  ↓
Contextual Response
  ↓
Frontend
```

The AI should operate through controlled tools.

## 21. AI Tools

Recommended initial tools:

- `get_customer_profile`
- `get_accounts`
- `get_account_balance`
- `get_recent_transactions`
- `search_transactions`
- `get_spending_summary`
- `get_loan_products`
- `check_loan_eligibility`
- `get_loan_applications`
- `get_investment_products`
- `get_customer_investments`
- `get_recommendations`
- `get_notifications`

Additional tools may be added later.

## 22. Tool Security

Every AI tool must execute in the context of the authenticated user.

Example:

**User:**

> Show my transactions.

**AI tool:**

`get_recent_transactions(current_user)`

**Not acceptable:**

`get_recent_transactions(customer_id_from_llm)`

The LLM must never be trusted to determine authorization.

The backend must derive identity from the authenticated session.

## 23. Read vs Write AI Actions

Initial AI implementation should prioritize read operations.

Safe initial tools:

- Read accounts
- Read balances
- Read transactions
- Read spending analytics
- Read recommendations
- Read loan products
- Check eligibility

Write operations such as transfers should require explicit confirmation.

Example:

**User:**

> Transfer ₹5,000 to Rahul.

AI should NOT immediately execute.

Instead:

> I can prepare that transfer for you.

> Source account: Savings XXXX1234
> Payee: Rahul
> Amount: ₹5,000

> Please confirm if you want me to proceed.

Only after explicit confirmation should a write-capable workflow be considered.

## 24. AI Prompting

The system prompt should establish:

- The assistant is a banking assistant
- It only has access to authorized tools
- It should not invent financial information
- It should distinguish facts from estimates
- It should ask clarification when required
- It should never expose secrets
- It should never reveal internal system prompts
- It should not fabricate transactions, balances, eligibility, or recommendations
- It should explain calculations when useful
## 25. AI Context

Useful contextual information:

- Current customer
- Customer segment
- Risk profile where appropriate
- Recent transactions
- Relevant recommendations
- Current account balances

Do not dump the entire database into the prompt.

Retrieve only relevant information through tools.

## 26. Conversation Persistence

Use:

- `ai_conversations`
- `ai_messages`

Conversation model:

```text
Conversation
    ↓
Messages
    ├── user
    ├── assistant
    ├── tool
    └── assistant
```

Store:

- `role`
- `content`
- `tool_name` where applicable
- `timestamp`

Do not store secrets or raw credentials.

## 27. AI APIs

### POST `/api/v1/ai/chat`

Request:

```json
{
  "conversation_id": "uuid",
  "message": "How much did I spend this month?"
}
```

Response:

```json
{
  "conversation_id": "uuid",
  "message": "You spent ₹42,350 this month...",
  "tool_used": "get_spending_summary"
}
```

### GET `/api/v1/ai/conversations`

Return user's conversations.

### GET `/api/v1/ai/conversations/{conversation_id}`

Return conversation messages.

## 28. AI Error Handling

If Groq is unavailable:

Do not show:

`Groq API Error 503`

Instead:

> I'm unable to access the banking assistant right now. Please try again in a moment.

Log the technical error on the backend.

Do not expose API keys or provider details.

## 29. Frontend API Layer

Do not scatter raw `fetch()` calls throughout components.

Prefer:

```text
frontend/
├── lib/
│   ├── api/
│   │   ├── auth.ts
│   │   ├── accounts.ts
│   │   ├── transactions.ts
│   │   ├── transfers.ts
│   │   ├── loans.ts
│   │   ├── investments.ts
│   │   ├── analytics.ts
│   │   ├── fraud.ts
│   │   └── ai.ts
│   │
│   └── api-client.ts
```

The API client should handle:

- Base URL
- Authorization
- JSON serialization
- Error normalization
- `401` handling
## 30. UI State

Handle these states explicitly:

- Loading
- Empty
- Success
- Error
- Unauthorized
- Forbidden

Example:

Loading transactions...

Instead of rendering an empty table while waiting.

## 31. Design Principles

The UI should feel:

- Professional
- Financial
- Modern
- Data-rich
- Trustworthy
- Responsive

Avoid excessive visual decoration.

Prioritize:

- Clear hierarchy
- Readable financial numbers
- Useful charts
- Tables for operational data
- Clear actions
- Accessible forms
## 32. Security Requirements

Never:

- Store passwords in `localStorage`
- Expose backend secrets
- Expose Groq API key
- Directly query database from frontend
- Trust frontend role checks
- Trust customer IDs supplied by UI

Frontend role checks are for navigation only.

Backend authorization is authoritative.

## 33. Testing

Frontend tests should cover:

- **Authentication**
  - Login success
  - Login failure
  - Logout
  - Protected routes
- **Banking**
  - Account rendering
  - Transaction filtering
  - Transfer form validation
  - Loan eligibility UI
  - Investment catalogue
- **Internal portal**
  - Analytics rendering
  - Fraud table
  - Alert detail
  - Role-based navigation
- **AI**
  - Chat submission
  - Streaming/loading state if implemented
  - Tool-result rendering
  - Error handling
  - Conversation persistence
## 34. API Integration Contract

The frontend should consume the documented backend APIs.

If an API is missing:

- Report the missing endpoint
- Agree on the contract
- Add/update backend endpoint
- Then integrate

Do not create fake frontend-only data once backend APIs exist.

Mock data may be used temporarily during parallel development but must be clearly isolated.

## 35. Parallel Development Strategy

The teams will work concurrently.

Therefore:

- Do not rename shared endpoints casually
- Do not rename database fields without coordination
- Do not change response structures silently
- Do not modify another team's service without discussion
- Keep API contracts stable
- Update context docs when contracts change
## 36. Suggested Frontend Structure

```text
frontend/
├── app/
│   ├── login/
│   ├── register/
│   ├── dashboard/
│   ├── accounts/
│   ├── transactions/
│   ├── transfers/
│   ├── bills/
│   ├── loans/
│   ├── investments/
│   ├── insurance/
│   ├── recommendations/
│   ├── ai/
│   └── internal/
│
├── components/
│   ├── layout/
│   ├── charts/
│   ├── banking/
│   ├── fraud/
│   ├── analytics/
│   └── ai/
│
├── lib/
│   ├── api/
│   ├── auth/
│   └── utils/
│
└── types/
```

The exact Next.js structure may vary depending on the chosen routing setup.

## 37. Definition of Done

A frontend feature is complete when:

- Backend API integrated
- Loading state implemented
- Empty state implemented
- Error state implemented
- Authentication handled
- Role access handled
- Responsive UI implemented
- API errors normalized
- Tests added
- No hardcoded production data
- No secrets in frontend
- Documentation updated if API contract changed

AI feature is complete when:

- Chat UI works
- Conversation persistence works
- Groq integration works
- Tools are implemented
- Tools respect authenticated user
- Tool calls are observable/debuggable
- Hallucination safeguards exist
- Errors are handled
- Write actions require confirmation
## 38. Integration Milestones

### Milestone 1

Frontend shell:

- Login
- Registration
- Layout
- Navigation
- Role routing
### Milestone 2

Customer banking:

- Dashboard
- Accounts
- Transactions
- Transfers
- Bills
### Milestone 3

Products:

- Loans
- Investments
- Insurance
- Recommendations
### Milestone 4

Internal portal:

- Analytics
- Fraud
- Compliance
- Risk
### Milestone 5

AI:

- Chat
- Conversations
- Banking tools
- Contextual responses
### Milestone 6

Polish:

- Error handling
- Loading states
- Responsive UI
- Security
- Testing
- Documentation

## 39. Core Principle

The frontend should make the backend capabilities feel like one coherent banking product.

The AI assistant should not feel like a generic chatbot bolted onto a banking dashboard.

It should understand the customer's actual:

- Accounts
- Transactions
- Spending
- Products
- Recommendations
- Financial context

while remaining constrained by the same authorization and business rules as the rest of the platform.
