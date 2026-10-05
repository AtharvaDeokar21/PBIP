# Credora Frontend

Responsive banking frontend built with Next.js App Router, React, TypeScript and Tailwind CSS. Credora uses a purple-and-white visual identity with shared layouts, Lucide icons and reusable UI components.

## Current experience

- **Landing page:** product cards, financial-insight sections and a custom home-and-savings illustration. The header offers Login and Sign up. Product cards and exploration buttons open customer sign-up.
- **Customer access:** login, sign-up, forgot-password and session-expired screens.
- **Admin access:** a separate login screen, accessible from the login-type switch. There is no public admin sign-up.
- **Customer workspace:** account overview, transactions, payments, payees, statements, schedules, loan and investment exploration, analytics, recommendations, notifications and settings.
- **Banking assistant:** a responsive chat panel with scripted responses and suggested questions.

The workspace uses sample data. Customer login validates fields locally and navigates to the workspace without sending credentials or starting an authenticated session. Sign-up, admin login and password recovery are not connected. Customer routes are public during development; no live banking operation is performed.

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

Unknown customer sections display a 404 page. Admin operational pages are not implemented.

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
        dashboard/page.tsx        Admin dashboard
        customers/page.tsx        Admin customer list
        customers/[id]/page.tsx   Admin customer details
        analytics/page.tsx        Admin analytics
      forgot-password/page.tsx    Recovery route
      session-expired/page.tsx    Session-expired route
      not-found.tsx               Not-found page
      portal/
        layout.tsx                Shared customer portal layout
        page.tsx                  Portal entry/redirect
        [section]/page.tsx        Customer section route registry
    components/
      auth-page.tsx               Customer/admin authentication screens
      portal-shell.tsx            Customer navigation, header and assistant
      customer-pages.tsx           Customer module implementations
      ui.tsx                      Shared brand, currency and UI primitives
      admin/                      Admin shell, pages, UI and data hooks
    lib/
      sample-data.ts              Illustrative customer data
      admin/
        types.ts                  Admin data types
        service.ts                Admin data access/service layer
        sample-data.ts            Fictional admin records
        metrics.ts                Admin analytics calculations
```

The `(workspace)` directory is a Next.js route group and does not appear in the public URL. Admin data currently comes from local sample-data services; there is no frontend API client yet.

## Team handoff

The Person 1 admin frontend now includes `/admin/dashboard`, `/admin/customers`, `/admin/customers/[id]` and `/admin/analytics`. These share typed fictional records through `src/lib/admin/service.ts`; backend integration remains pending. Admin components and scoped styles are separate from the customer portal. `tests/admin.spec.ts` covers navigation, filters, pagination, details and responsive layouts.

- Read the [feature tracker](../docs/FRONTEND_FEATURE_TRACKER.md) before claiming work. Mark the interface and API integration separately.
- Follow the [design system](../docs/FRONTEND_DESIGN_SYSTEM.md) for colors, typography and shared components.
- Coordinate changes to `globals.css`, `ui.tsx` and the customer shell, which affect multiple pages.
- Split a customer module into its own component before two developers work independently in `customer-pages.tsx`.
- Continue internal modules under `src/app/admin/` and reuse `src/components/admin/`. Admin login opens the workspace without backend authentication or access control.

## Connecting the backend

The FastAPI backend exposes the endpoints listed below, but the frontend does not call them yet. The current interface uses sample data and local-only interactions.

Integration work includes an agreed API/service layer, secure session handling, server-enforced authorization, protected routes, loading/error/retry states and replacing fixtures with consistent live records. Coordinate the frontend origin with backend CORS configuration: the frontend scripts bind to `127.0.0.1`, while the current backend allowlist uses `localhost` origins.

Do not place real customer information behind the current public routes. Keep secrets server-side and follow the repository's review rule for shared API or schema changes.

## Backend API endpoints

The API is served by FastAPI. The development base URL is `http://localhost:8000`, and the versioned routes use the `/api/v1` prefix. For example, `GET /api/v1/accounts` is available at `http://localhost:8000/api/v1/accounts`. The backend's interactive API documentation is at `http://localhost:8000/docs`.

When frontend integration is implemented, configure the API base URL through an environment variable such as `NEXT_PUBLIC_API_URL` rather than hardcoding it in components. No API client or such environment variable is currently required by this sample-data UI.

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
| Fraud | `GET` | `/api/v1/fraud/customers/{customer_id}/risk` | Get customer fraud risk; Fraud Analyst or Admin |
| Compliance | `GET` | `/api/v1/compliance/alerts` | List compliance alerts; Compliance Officer or Admin |
| Compliance | `GET` | `/api/v1/compliance/audit-logs` | List audit logs; Compliance Officer or Admin |
| Compliance | `GET` | `/api/v1/compliance/security-events` | List security events; Compliance Officer or Admin |
| AI assistant | `POST` | `/api/v1/ai/chat` | Submit a chat message |
| AI assistant | `GET` | `/api/v1/ai/conversations` | List conversations |

The analytics, fraud, compliance and AI handlers currently return placeholder responses. The AI API currently has no conversation-detail route. Check the backend's `/docs` and response schemas when integrating; this table describes the routes, not a guarantee that every workflow is complete. Use the backend OpenAPI contract for exact request/response fields.
