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
src/
  app/
    page.tsx                      Landing page
    layout.tsx                    Metadata and global layout
    globals.css                   Design tokens, layouts and responsive styles
    login/                        Customer login route
    register/                     Customer sign-up route
    admin/login/                  Admin login route
    forgot-password/              Recovery route
    session-expired/              Session-expired route
    portal/
      layout.tsx                  Shared customer shell
      [section]/page.tsx          Customer route registry
  components/
    auth-page.tsx                 Customer/admin authentication screens
    portal-shell.tsx              Navigation, header and assistant
    customer-pages.tsx            Customer module implementations
    ui.tsx                        Brand, currency and shared primitives
  lib/
    sample-data.ts                Illustrative accounts, transactions and products
tests/customer.spec.ts            Browser checks
playwright.config.ts              Test server and browser configuration
```

## Team handoff

- Read the [feature tracker](../docs/FRONTEND_FEATURE_TRACKER.md) before claiming work. Mark the interface and API integration separately.
- Follow the [design system](../docs/FRONTEND_DESIGN_SYSTEM.md) for colors, typography and shared components.
- Coordinate changes to `globals.css`, `ui.tsx` and the customer shell, which affect multiple pages.
- Split a customer module into its own component before two developers work independently in `customer-pages.tsx`.
- Add internal operational pages under `src/app/admin/` and separate admin components. The existing login screen does not implement admin access control.

## Connecting the backend

The FastAPI backend has registration, login and current-user endpoints. The frontend does not call them yet, and inspected account/transfer endpoints are placeholders.

Integration work includes an agreed API/service layer, secure session handling, server-enforced authorization, protected routes, loading/error/retry states and replacing fixtures with consistent live records. Coordinate the frontend origin with backend CORS configuration: the frontend scripts bind to `127.0.0.1`, while the current backend allowlist uses `localhost` origins.

Do not place real customer information behind the current public routes. Keep secrets server-side and follow the repository's review rule for shared API or schema changes.
