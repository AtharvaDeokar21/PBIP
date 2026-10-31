# Credora Frontend

Responsive banking frontend built with Next.js App Router, React, TypeScript and Tailwind CSS. Credora uses a purple-and-white visual identity with shared layouts, Lucide icons and reusable UI components.

## Current experience

- **Landing page:** product cards, financial-insight sections and a custom home-and-savings illustration. The header offers Login and Sign up. Product cards and exploration buttons open customer sign-up.
- **Customer access:** login, sign-up, forgot-password and session-expired screens.
- **Admin access:** a separate login screen, accessible from the login-type switch. There is no public admin sign-up.
- **Customer workspace:** account overview, transactions, payments, payees, statements, schedules, loan and investment exploration, analytics, recommendations, notifications and settings.
- **Admin workspace:** operational internal console featuring an executive overview dashboard, customer directory with 360° profiles, behavioral & transaction analytics, real-time fraud monitoring & rule engine, fraud investigation case management with SAR filing, AML compliance & sanctions screening, and cryptographic audit vault with security events.
- **Banking assistant:** a responsive chat panel with scripted responses and suggested questions.

The workspace uses sample data. Customer login validates fields locally and navigates to the workspace without sending credentials or starting an authenticated session. Sign-up, admin login and password recovery are not connected. Routes are accessible during development; no live banking operation is performed.

## Local setup

Use Node.js and npm; Node.js 24 was used during development. From the repository root:

```powershell
cd frontend
npm ci
npm run dev
```

Open [http://127.0.0.1:3000](http://127.0.0.1:3000). No frontend environment variables or running backend are required for the current interface.

To serve a production build, stop the development server and run:

```powershell
npm run build
npm start
```

## Routes

| Route | Screen |
| --- | --- |
| `/` | Landing page |
| `/login` | Customer login |
| `/register` | Customer sign-up |
| `/admin/login` | Admin login |
| `/forgot-password` | Password recovery |
| `/session-expired` | Session-expired screen |
| `/portal` | Redirect to customer overview |
| `/portal/dashboard` | Balances, quick actions, spending and recent activity |
| `/portal/accounts` | Accounts, details and transaction filters |
| `/portal/payments` | Transfer form, review, verification and result |
| `/portal/payments?tab=bills` | Bill-payment flow |
| `/portal/payees` | Payee list and local add/edit/remove actions |
| `/portal/statements` | Statement filters, preview and printing |
| `/portal/scheduled` | Upcoming payment previews |
| `/portal/loans` | Loan categories and EMI calculator |
| `/portal/wealth` | Investment categories and product comparison |
| `/portal/analytics` | Spending and income charts |
| `/portal/recommendations` | Illustrative product suggestions |
| `/portal/notifications` | Notifications and transaction-report previews |
| `/portal/settings` | Profile and notification preferences |
| `/admin` | Redirect to admin dashboard |
| `/admin/dashboard` | Admin executive KPIs, workload queue and risk heatmaps |
| `/admin/customers` | Admin customer directory, search and status filters |
| `/admin/customers/[id]` | Admin customer 360° dossier, accounts, loans and risk metrics |
| `/admin/analytics` | Admin transaction volume, velocity charts and cohort analytics |
| `/admin/fraud` | Real-time fraud detection alerts, risk score distribution and rule engine |
| `/admin/investigations` | Fraud case management, dossier timeline, evidence locker and SAR filing |
| `/admin/compliance` | Regulatory compliance, AML transaction monitoring, sanctions/PEP watchlist and reporting |
| `/admin/audit-logs` | Cryptographic audit trail vault, SHA-256 hash verification and security event logs |

Unknown customer or admin sections display a 404 page. Both customer and administrative operational workspaces are fully functional with interactive workflows and local reactive states.

## Implemented interactions and limits

| Module | Available behavior | Integration still needed |
| --- | --- | --- |
| Accounts | Account selection; transaction search, date/category/type/amount filters and sorting | Live balances, records and pagination |
| Payments | Amount/balance/limit validation, review and sample OTP `123456` | Actual transfers, live verification, processing, receipts and persisted schedules |
| Payees | Add, edit and confirm removal in page state | Beneficiary verification, persistence and shared transfer-payee source |
| Statements | Account and period filtering, custom dates, browser Print / Save as PDF | Official bank-generated statements and complete transaction data |
| Schedules | Sample upcoming payments, date edit and cancellation confirmation | Durable changes and scheduled execution |
| Loans | Product categories, existing-loan summary and EMI calculator | Eligibility, multi-step applications, uploads and tracking |
| Wealth | Product categories, detail notices and comparison of up to three categories | Provider data, holdings and investment transactions |
| Insights | Illustrative charts and static recommendations | Live aggregation and personalized recommendations |
| Assistant | Scripted replies, suggested prompts and local chat history | Live AI, streaming and persistent conversations |
| Notifications/settings | Read/report controls, profile form and preference controls | Saved preferences, real fraud reporting and account security controls |
| Admin Customers | Search, filter, pagination, customer profile view, risk score badges | Live customer database sync, CRM notes integration |
| Admin Analytics | Date-range filtering, transaction volume, revenue metrics and cohort charts | Real-time streaming analytics pipeline, data warehouse querying |
| Fraud Monitoring | Alert triage, severity filter, one-click containment (freeze account, card block, dismiss), rule toggle & threshold edits | Live WebSocket alert ingestion, automated containment triggers, rule persistence |
| Fraud Investigations | Case dossier view, suspicious transaction selection, evidence notes, activity timeline, interactive SAR filing modal | FinCEN/FIU electronic filing, persistent dossier updates, S3 document storage |
| Compliance & AML | AML alert queue, MLRO escalation, automated SAR draft, sanctions/PEP watchlist screening, regulatory reporting | Live AML rules engine, automated sanction list sync (OFAC/EU/UN), automated PDF export |
| Audit Vault | Cryptographic SHA-256 tamper-evident log inspection, filter by actor/service, live integrity verification, security incident log & IP containment | Centralized SIEM forwarding, distributed ledger / external timestamping anchor |

Payee, schedule, profile and notification changes reset when their pages unmount. Chat history remains within the mounted customer shell and resets when that shell unmounts. Sample totals are illustrative and are not derived from the short transaction fixture list.

## Scripts

Run from `frontend/`:

| Command | Purpose |
| --- | --- |
| `npm run dev` | Start the development server at `127.0.0.1:3000` |
| `npm run build` | Create the production build |
| `npm start` | Serve the existing production build |
| `npm run typecheck` | Check TypeScript |
| `npm run format:check` | Check source formatting |
| `npm run format` | Apply Prettier formatting |
| `npm run test:e2e` | Run Playwright browser checks |

## Browser checks

Install Chromium once, then build and run the checks:

```powershell
npx playwright install chromium
npm run build
npm run test:e2e
```

Alternatively, use an existing Microsoft Edge installation on Windows:

```powershell
$env:CREDORA_BROWSER_CHANNEL = 'msedge'
npm run build
npm run test:e2e
```

Playwright starts `npm start` automatically. Outside CI it can reuse a server already running on port 3000; stop that server first when you want to verify a fresh production build. Screenshots and failure details are written to the ignored `test-results/` directory.

Checks cover navigation, desktop/mobile layouts, account filtering, payment validation and OTP, bill routing, payee changes, statement periods, EMI calculations, comparison controls, the scripted assistant and authentication-screen behavior. These are interface checks, not proof of production authentication or banking correctness.

## Source structure

```text
frontend/
  package.json                    Scripts and dependencies
  next.config.ts                  Next.js configuration
  playwright.config.ts            Browser-test configuration
  tests/
    customer.spec.ts               Customer portal browser checks
    admin.spec.ts                  Admin portal browser checks
  src/
    app/
      page.tsx                    Landing page
      layout.tsx                  Metadata and global layout
      globals.css                 Design tokens, layouts and responsive styles
      login/page.tsx              Customer login route
      register/page.tsx           Customer sign-up route
      admin/login/page.tsx        Admin login route
      admin/(workspace)/          Admin workspace route group
        layout.tsx                Admin shell layout
        admin.css                 Admin-scoped styles and tokens
        dashboard/page.tsx        Admin dashboard
        customers/page.tsx        Admin customer list
        customers/[id]/page.tsx   Admin customer details
        analytics/page.tsx        Admin analytics
        fraud/page.tsx            Admin fraud detection & security
        investigations/page.tsx   Admin fraud case investigations & SAR
        compliance/page.tsx       Admin compliance & AML monitoring
        audit-logs/page.tsx       Admin audit vault & security events
      forgot-password/page.tsx    Recovery route
      session-expired/page.tsx    Session-expired route
      not-found.tsx               Not-found page
      portal/
        layout.tsx                Shared customer portal layout
        page.tsx                  Portal entry/redirect
        [section]/page.tsx        Customer section route registry
    components/
      auth-page.tsx               Customer/admin authentication screens
      customer-pages.tsx           Customer module implementations with live API integration
      use-customer-api.ts          React hooks for customer banking resources
      ui.tsx                      Shared brand, currency and UI primitives
      admin/                      Admin workspace components
        shell.tsx                 Admin navigation, breadcrumb & staff header
        fraud-security.tsx        Fraud alerts, rules engine & containment actions
        fraud-investigation.tsx   Investigation dossier, evidence & SAR modal
        compliance-risk.tsx       AML monitoring, watchlist & regulatory reports
        audit-logs.tsx            Cryptographic SHA-256 vault & security events
    lib/
      sample-data.ts              Illustrative customer data
      customer/
        api.ts                    Typed customer API client for all customer banking endpoints
      admin/
        types.ts                  Admin data types
        service.ts                Admin data access/service layer
        sample-data.ts            Fictional admin records
        metrics.ts                Admin analytics calculations
```

The `(workspace)` directory is a Next.js route group and does not appear in the public URL.

## Customer Portal Backend Integration

The customer-facing portal is fully wired to the FastAPI backend with typed API clients and React resource hooks:
- **Client & Hook Architecture**:
  - `src/lib/customer/api.ts`: Typed Fetch API client mirroring every endpoint in `docs/api/customer/` with automatic Bearer token injection from `localStorage`. Base URL configured via `NEXT_PUBLIC_API_URL`; set it to the API gateway, `http://localhost:8080/api/v1` (Docker sets this at build time).
  - `src/components/use-customer-api.ts`: Reusable React data hooks (`useCustomerSummary`, `useCustomerProfile`, `useAccounts`, `useTransactions`, `usePayees`, `useTransfers`, `useBillers`, `useLoanProducts`, `useHoldings`, etc.) with loading, error, and refresh mechanics.
  - `src/components/customer-pages.tsx`: Connected to live data while maintaining seamless offline/demo fallbacks for unauthenticated or local development without a running backend.
- **Implemented Customer Workflows**:
  - **Authentication**: Customer Login (`/auth/login`) and Sign-up (`/auth/register`) with JWT session persistence in `localStorage`.
  - **Financial Summary**: Dashboard aggregates live balances, invested funds, and spending trends from `/customers/me/summary` and `/customers/me`.
  - **Account Services**: Live account listing (`/accounts`) and filterable transaction history (`/accounts/{id}/transactions`) with pagination and search.
  - **Payments & Transfers**: Account-to-account immediate and scheduled transfers (`/transfers`) and utility bill payments (`/bills/pay`, `/billers`).
  - **Beneficiary Management**: Full CRUD operations for payees (`/payees`).
  - **Loans & Credit**: Product catalogue (`/loans/products`), EMI calculator, eligibility assessment (`/loans/eligibility`), and application submission (`/loans/applications`).
  - **Wealth & Investments**: Product discovery (`/investments/products`), portfolio holdings (`/investments`), and simulated purchase execution.
  - **Recommendations & Profile**: AI-driven recommendations (`/recommendations`) and profile self-service editing (`/customers/me`).

## Team handoff

The internal admin portal now covers all core banking operations:
- `/admin/dashboard`: Executive KPI stats, high-risk queue, and activity stream.
- `/admin/customers` and `/admin/customers/[id]`: Customer directory with search/filters and 360° profile view.
- `/admin/analytics`: Transaction volumes, customer growth cohorts and risk trends.
- `/admin/fraud`: Real-time fraud detection alerts, risk score distribution, one-click containment (freeze account, card block, dismiss), and dynamic rule engine with threshold adjustments.
- `/admin/investigations`: Fraud case management, suspicious transaction evidence linking, investigator notes, activity timeline, and interactive SAR (Suspicious Activity Report) filing modal.
- `/admin/compliance`: Regulatory compliance, AML transaction monitoring, high-risk flag queues, MLRO escalation, automated sanctions/PEP watchlist search, and periodic regulatory report generation.
- `/admin/audit-logs`: Cryptographic SHA-256 tamper-evident audit vault with actor/service filters, real-time integrity verification check, and security incident response logs.

All modules share design system conventions with dark cyber tokens, interactive modal dialogs, and scoped styles in `src/app/admin/(workspace)/admin.css`.

- Read the [feature tracker](../docs/FRONTEND_FEATURE_TRACKER.md) before claiming work. Mark the interface and API integration separately.
- Follow the [design system](../docs/FRONTEND_DESIGN_SYSTEM.md) for colors, typography and shared components.
- Coordinate changes to `globals.css`, `ui.tsx` and the customer shell, which affect multiple pages.
- Split a customer module into its own component before two developers work independently in `customer-pages.tsx`.
- Continue internal modules under `src/app/admin/` and reuse `src/components/admin/`. Admin login opens the workspace without backend authentication or access control.

## Connecting the backend

The FastAPI backend exposes the endpoints listed below, but the frontend does not call them yet. The current interface uses sample data and local-only interactions.

Integration work includes an agreed API/service layer, secure session handling, server-enforced authorization, protected routes, loading/error/retry states and replacing fixtures with consistent live records.

Do not place real customer information behind the current public routes. Keep secrets server-side and follow the repository's review rule for shared API or schema changes.

## Backend API endpoints

The API is served by the FastAPI customer and admin services behind the nginx API gateway. The development base URL is `http://localhost:8080`, and the versioned routes use the `/api/v1` prefix. For example, `GET /api/v1/accounts` is available at `http://localhost:8080/api/v1/accounts`. Interactive API documentation is at `http://localhost:8001/docs` (customer-service) and `http://localhost:8002/docs` (admin-service).

Unless marked public, endpoints require a bearer access token returned by `POST /api/v1/auth/login`. Customer endpoints additionally require a customer identity; internal endpoints enforce their listed roles. The API is the authority for access control.

| Area | Method | Endpoint | Purpose / access |
| --- | --- | --- | --- |
| Health | `GET` | `/api/v1/health` | Health and database status; public |
| Authentication | `POST` | `/api/v1/auth/register` | Register a customer; public |
| Authentication | `POST` | `/api/v1/auth/login` | Authenticate and return an access token; public |
| Current user | `GET` | `/api/v1/me` | Return the authenticated user |
| Customer | `GET` | `/api/v1/customers/me` | Get the current customer's profile |
| Customer | `PATCH` | `/api/v1/customers/me` | Update the current customer's profile |
| Customer | `GET` | `/api/v1/customers/me/summary` | Get the current customer's financial summary |
| Accounts | `GET` | `/api/v1/accounts` | List the current customer's accounts |
| Accounts | `GET` | `/api/v1/accounts/{account_id}` | Get an account |
| Accounts | `GET` | `/api/v1/accounts/{account_id}/transactions` | List an account's transactions; supports transaction filters/pagination |
| Transactions | `GET` | `/api/v1/transactions/{transaction_id}` | Get a transaction |
| Payees | `POST` | `/api/v1/payees` | Create a payee |
| Payees | `GET` | `/api/v1/payees` | List payees |
| Payees | `PATCH` | `/api/v1/payees/{payee_id}` | Update a payee |
| Payees | `DELETE` | `/api/v1/payees/{payee_id}` | Delete a payee |
| Transfers | `POST` | `/api/v1/transfers` | Create a transfer |
| Transfers | `GET` | `/api/v1/transfers` | List transfers; supports `page`, `page_size` and `status` |
| Transfers | `GET` | `/api/v1/transfers/{transfer_id}` | Get a transfer |
| Transfers | `POST` | `/api/v1/transfers/{transfer_id}/cancel` | Cancel a transfer |
| Bills | `GET` | `/api/v1/billers` | List billers; supports `category` and `provider_code` filters |
| Bills | `POST` | `/api/v1/bills/pay` | Pay a bill |
| Bills | `GET` | `/api/v1/bills/history` | List bill-payment history; supports `page` and `page_size` |
| Loans | `GET` | `/api/v1/loans/products` | List loan products; supports `loan_type` filter |
| Loans | `GET` | `/api/v1/loans/products/{product_id}` | Get a loan product |
| Loans | `POST` | `/api/v1/loans/eligibility` | Check the current customer's loan eligibility |
| Loans | `POST` | `/api/v1/loans/applications` | Submit a loan application |
| Loans | `GET` | `/api/v1/loans/applications` | List the current customer's loan applications |
| Loans | `GET` | `/api/v1/loans/applications/{application_id}` | Get a loan application |
| Investments | `GET` | `/api/v1/investments/products` | List investment products; supports `product_type` and `risk_level` filters |
| Investments | `GET` | `/api/v1/investments/products/{product_id}` | Get an investment product |
| Investments | `GET` | `/api/v1/investments` | List the current customer's holdings |
| Investments | `POST` | `/api/v1/investments` | Purchase an investment |
| Insurance | `GET` | `/api/v1/insurance/products` | List insurance products; supports `insurance_type` and `risk_level` filters |
| Insurance | `GET` | `/api/v1/insurance/products/{product_id}` | Get an insurance product |
| Recommendations | `GET` | `/api/v1/recommendations` | List recommendations for the current customer |
| Analytics | `GET` | `/api/v1/analytics/overview` | Internal analytics overview; Relationship Manager or Admin |
| Analytics | `GET` | `/api/v1/analytics/customers` | Internal customer analytics; Relationship Manager or Admin |
| Analytics | `GET` | `/api/v1/analytics/transactions` | Internal transaction analytics; Relationship Manager or Admin |
| Fraud | `GET` | `/api/v1/fraud/alerts` | List fraud alerts; Fraud Analyst or Admin |
| Fraud | `GET` | `/api/v1/fraud/alerts/{alert_id}` | Get a fraud alert; Fraud Analyst or Admin |
| Fraud | `POST` | `/api/v1/fraud/alerts/{alert_id}/action` | Trigger containment (freeze account, block card, dismiss) |
| Fraud | `GET` | `/api/v1/fraud/rules` | List fraud detection rules and velocity thresholds |
| Fraud | `PATCH` | `/api/v1/fraud/rules/{rule_id}` | Toggle rule active status and update risk threshold |
| Fraud | `GET` | `/api/v1/fraud/customers/{customer_id}/risk` | Get customer fraud risk score and factors |
| Investigations | `GET` | `/api/v1/fraud/cases` | List fraud investigation cases; supports status/severity filters |
| Investigations | `POST` | `/api/v1/fraud/cases` | Open a new fraud investigation case dossier |
| Investigations | `GET` | `/api/v1/fraud/cases/{case_id}` | Retrieve case dossier, suspect details and flagged transactions |
| Investigations | `PATCH` | `/api/v1/fraud/cases/{case_id}` | Update case status, assign investigator, add notes |
| Investigations | `POST` | `/api/v1/fraud/cases/{case_id}/evidence` | Attach investigation evidence note or document |
| Investigations | `POST` | `/api/v1/fraud/cases/{case_id}/sar` | Submit FinCEN/FIU Suspicious Activity Report (SAR) |
| Compliance | `GET` | `/api/v1/compliance/alerts` | List AML compliance alerts; Compliance Officer or Admin |
| Compliance | `POST` | `/api/v1/compliance/alerts/{alert_id}/resolve` | Escalate alert to MLRO or mark as cleared false-positive |
| Compliance | `POST` | `/api/v1/compliance/watchlist/screen` | Screen individual or transaction against OFAC/EU/UN PEP sanctions |
| Compliance | `GET` | `/api/v1/compliance/reports` | List generated AML and regulatory filing reports |
| Compliance | `POST` | `/api/v1/compliance/reports/generate` | Trigger generation of periodic regulatory report (AML, CTR, PEP) |
| Audit Vault | `GET` | `/api/v1/compliance/audit-logs` | List tamper-evident audit logs; Compliance Officer or Admin |
| Audit Vault | `POST` | `/api/v1/compliance/audit-logs/verify` | Verify cryptographic SHA-256 hash chain against anchor |
| Audit Vault | `GET` | `/api/v1/compliance/audit-logs/export` | Export signed regulatory audit bundle (JSON/CSV) |
| Audit Vault | `GET` | `/api/v1/compliance/security-events` | List security incident logs; Compliance Officer or Admin |
| Audit Vault | `POST` | `/api/v1/compliance/security-events/{event_id}/remediate` | Trigger incident containment (block IP, revoke session token) |
| AI assistant | `POST` | `/api/v1/ai/chat` | Submit a chat message |
| AI assistant | `GET` | `/api/v1/ai/conversations` | List conversations |

The analytics, fraud, compliance and AI handlers currently return placeholder responses. The AI API currently has no conversation-detail route. Check the backend's `/docs` and response schemas when integrating; this table describes the routes, not a guarantee that every workflow is complete. Use the backend OpenAPI contract for exact request/response fields.

### Required Backend API Specifications for Admin Integration

To wire the newly created admin operational pages to the FastAPI backend, the following endpoint schemas and payloads are specified:

#### 1. Fraud Prevention & Detection (`/admin/fraud`)
- **`POST /api/v1/fraud/alerts/{alert_id}/action`**
  - **Payload**:
    ```json
    {
      "action": "FREEZE_ACCOUNT" | "BLOCK_CARD" | "DISMISS" | "ESCALATE",
      "reason": "String explaining analyst justification",
      "analyst_id": "usr_admin_001"
    }
    ```
  - **Response**: `{ "status": "SUCCESS", "alert_id": "...", "timestamp": "..." }`
- **`GET /api/v1/fraud/rules`**
  - **Response**: Array of detection rules with `rule_id`, `name`, `category`, `threshold_value`, `risk_weight`, and `is_active` boolean.
- **`PATCH /api/v1/fraud/rules/{rule_id}`**
  - **Payload**: `{ "is_active": boolean, "threshold_value": number }`

#### 2. Fraud Investigations & Case Management (`/admin/investigations`)
- **`GET /api/v1/fraud/cases`**
  - **Query Params**: `status` (`OPEN`, `IN_REVIEW`, `SUBMITTED_SAR`, `CLOSED`), `severity` (`CRITICAL`, `HIGH`, `MEDIUM`), `assignee_id`
- **`POST /api/v1/fraud/cases/{case_id}/sar`**
  - **Payload**:
    ```json
    {
      "fincen_reference": "SAR-2026-X99",
      "narrative": "Detailed summary of suspicious transaction structuring...",
      "suspect_id": "cust_001",
      "total_amount_flagged": 185000.00,
      "currency": "GBP",
      "violation_types": ["MONEY_LAUNDERING", "STRUCTURING"]
    }
    ```
- **`POST /api/v1/fraud/cases/{case_id}/evidence`**
  - **Payload**: `{ "title": string, "notes": string, "file_url"?: string, "transaction_ids": string[] }`

#### 3. Regulatory Compliance & AML Monitoring (`/admin/compliance`)
- **`POST /api/v1/compliance/alerts/{alert_id}/resolve`**
  - **Payload**: `{ "resolution": "ESCALATED_MLRO" | "FILED_SAR" | "DISMISSED_FALSE_POSITIVE", "notes": string }`
- **`POST /api/v1/compliance/watchlist/screen`**
  - **Payload**: `{ "query_name": string, "country"?: string, "dob"?: string, "threshold": 0.85 }`
  - **Response**: List of match hits with confidence score, sanctions list source (OFAC/EU/UN), and entity type (PEP/Sanctioned).
- **`POST /api/v1/compliance/reports/generate`**
  - **Payload**: `{ "report_type": "AML_MONTHLY" | "CTR_BATCH" | "PEP_AUDIT", "period": "2026-Q1" }`
  - **Response**: `{ "report_id": string, "status": "GENERATING" | "READY", "download_url": string }`

#### 4. Cryptographic Audit Vault & Security Incident Log (`/admin/audit-logs`)
- **`POST /api/v1/compliance/audit-logs/verify`**
  - **Payload**: `{ "from_timestamp": string, "to_timestamp": string }`
  - **Response**:
    ```json
    {
      "verified": true,
      "merkle_root": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "records_checked": 240,
      "tampered_records": []
    }
    ```
- **`POST /api/v1/compliance/security-events/{event_id}/remediate`**
  - **Payload**: `{ "action": "BLOCK_IP" | "TERMINATE_SESSION" | "REVOKE_TOKEN" | "FORCE_MFA" }`
