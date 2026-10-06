# Credora frontend delivery & team handoff

Last updated: 26 September 2026.

This is the shared source of truth for frontend ownership and progress. Scope comes from the supplied feature breakdown; its embedded citation placeholders are not independently verified requirements. The original use-case document was not included. Match this list to that document before final submission.

## Read the status correctly

- **UI DONE**: the specified interface or interaction works with sample data. It is not production banking functionality.
- **PARTIAL**: a usable starting point exists, with explicitly listed work remaining.
- **TODO**: not implemented; available for assignment.
- **INTEGRATION TODO**: requires real API data, server authorization, validation and error handling.

Current allocation: **Developer A (this implementation)** owns the landing page, customer shell and customer sample foundation. **Developer B (suggested, not yet assigned)** can own the internal portal and/or claim outstanding customer modules below. Do not duplicate DONE interfaces. Claim a row by adding your name and changing its status to IN PROGRESS before editing.

All customer routes below are intentionally public sample routes. They do not protect real customer information. No payment, bank account, registration, recovery email, fraud case or investment is created by these screens. Local preview edits reset on navigation. Sample aggregates are illustrative and are not derived from the short transaction fixture list.

## Shared foundation

| Feature | Status | Implementation / remaining work | Owner |
| --- | --- | --- | --- |
| Next.js App Router, TypeScript, Tailwind | UI DONE | `frontend/`; scripts for dev, build, typecheck | A |
| Purple / white design system | UI DONE | `src/app/globals.css`; see `FRONTEND_DESIGN_SYSTEM.md` | A |
| Customer sidebar, header, breadcrumbs, mobile navigation | UI DONE | `src/components/portal-shell.tsx` | A |
| Icons, brand, section titles, INR formatting | UI DONE | `src/components/ui.tsx`; Lucide icon set | A |
| Empty states, focus outlines, native field validation, reduced motion | UI DONE | Present in implemented flows; full accessibility audit remains | A |
| Global loading, network failure, retry and offline UI | TODO | Implement alongside real API integration | Unassigned |
| API client, authenticated session, server-side route protection | INTEGRATION TODO | No credentials or tokens are currently collected or persisted | Unassigned |
| Admin shell and role-aware navigation | TODO | Use shared tokens; enforce access on server/API too | Suggested B |
| 404 page | UI DONE | `src/app/not-found.tsx` | A |

## Customer portal

### 1. Landing & authentication

Visual update: replaced the decorative “your next.” lettering in the purple goal banner with a custom home-and-savings illustration.

Header cleanup: the landing header offers only **Login** and **Sign up**; the admin link was removed from the landing page (admin access remains available on the login-type switch). Removed the customer-shell sample-data banner and sidebar reminder card.

Landing update: removed the “YOUR MONEY. MORE POSSIBILITIES.” and “YOUR MONTH, UNDERSTOOD” labels. All product cards and exploration CTAs now lead to customer sign-up (`/register`), while customer/admin login links retain their separate destinations.

Latest update: customer login (`/login`) and sign-up (`/register`) have separate entry points from admin login (`/admin/login`). Customer login validates locally and opens the public sample workspace without sending credentials or creating an authenticated session. Sign-up, admin login and password recovery remain unavailable pending backend integration. The former “demo” wording has been removed from the interface; illustrative data and simulated payment behavior remain identified as samples.

| Feature / route | Status | What exists / what remains |
| --- | --- | --- |
| Landing `/` | UI DONE | Responsive hero, product sections, money insights illustration, CTA, footer, customer entry points |
| Login `/login` | PARTIAL | Customer email/password form, visibility toggle and customer/admin switch; customer submit opens the public sample workspace only, while actual authentication and session management are pending |
| Register `/register` | PARTIAL | Customer-only first/last name, email and password form; no real registration or KYC/onboarding |
| Admin login `/admin/login` | PARTIAL | Separate administrator email/password form, no public sign-up, unavailable-service feedback; authentication and role enforcement pending |
| Forgot password `/forgot-password` | PARTIAL | Form and honest preview result; recovery email and reset-token journey pending |
| Login OTP/MFA | TODO | Payment sample code is not login MFA; challenge, resend, expiry, attempts and recovery flows needed |
| Logout | PARTIAL | Returns to customer login; authenticated session invalidation pending |
| Session expired `/session-expired` | PARTIAL | Screen built; token expiry detection and redirect pending |
| Failed login / lockout / security events | INTEGRATION TODO | Backend already records login events; connect frontend errors without leaking account existence |

### 2. Dashboard `/portal/dashboard` — UI DONE (A)

- [x] Total, savings and current balances.
- [x] Investments and outstanding loan summaries.
- [x] Transfer, bills, statements, investing and loan quick links.
- [x] Recent transaction table and account navigation.
- [x] Category spending chart with text alternative and legend.
- [x] Financial wellbeing score, sample insight and recommendation.
- [ ] Live aggregation, date ranges, financial health methodology and personalization.
- [ ] Account-data loading, unavailable-data and API error states.

### 3. Accounts `/portal/accounts` — UI DONE (A)

- [x] Savings/current cards, masked numbers, status and balances.
- [x] Select an account for holder, masked number, branch and illustrative IFSC.
- [x] Transaction filtering by account, search, dates, credit/debit, category, amount range.
- [x] Newest/oldest/highest-amount sort and no-results state.
- [ ] Dedicated shareable account details route if required by API/navigation design.
- [ ] Pagination, live records and account settings.

### 4. Statements `/portal/statements` — PARTIAL (A)

- [x] Account and 1/3/6-month selections; custom date range validation.
- [x] Filtered statement view with sample-only notice.
- [x] Print layout; browser Print / Save as PDF action.
- [ ] Official server-generated PDF download with opening/closing balances, all records, immutable statement metadata and authorization.
- [ ] Download progress, failure and retry states.

Browser save-as-PDF is an interim frontend convenience, not the official PDF statement requirement.

### 5. Payments `/portal/payments` — PARTIAL (A)

- [x] From-account selection, sample payees, amount, remarks, optional schedule date.
- [x] Positive amount, available balance and sample transfer-limit checks.
- [x] Editable review step before confirmation.
- [x] Sample OTP `123456`; invalid code feedback; confirmation result.
- [ ] Real payee source and live balances.
- [ ] Backend-created transfer, idempotency, live OTP, processing state and durable receipt.
- [ ] Server fraud rejection, timeout, retry, failed transfer and limit-specific states.
- [ ] Persist scheduled transfers and show them on Scheduled payments.

### 6. Payees `/portal/payees` — PARTIAL (A)

- [x] Sample list, add, edit and confirmation before removal.
- [x] Name/bank and last-four-digit validation for preview.
- [ ] Full account and IFSC validation, bank/beneficiary verification, OTP, cooling period if required.
- [ ] Durable CRUD and shared payee source for transfers. Page preview changes intentionally do not change transfer options.

### 7. Bill payments `/portal/payments?tab=bills` — PARTIAL (A)

- [x] Electricity, mobile, internet, gas, credit-card and other categories.
- [x] Reference input, amount, review, sample OTP and result.
- [ ] Provider/biller list, bill fetch, customer details and fetched amount verification.
- [ ] Payment execution, downloadable receipt and bill payment history.

### 8. Scheduled payments `/portal/scheduled` — PARTIAL (A)

- [x] Illustrative recurring payments and next dates.
- [x] Date edit and confirmation before cancellation in local page state.
- [ ] Persist updates, change amount/recurrence/end date, distinguish transfer vs bill schedule.
- [ ] Backend execution status, upcoming vs failed vs completed filters.

### 9. Loans `/portal/loans` — PARTIAL (A)

- [x] Personal, home, education and vehicle catalogue with introductory details.
- [x] Interactive EMI calculator (amount, annual rate, tenure); total interest and zero-interest handling.
- [x] Existing-loan summary with illustrative next EMI.
- [ ] Full product details and bank-supplied rates/terms.
- [ ] Eligibility checker (income, employment, existing EMI, requested amount, tenure).
- [ ] Multi-step application: personal → financial → loan → documents → review → submit.
- [ ] Upload validation, application save/resume and submission states.
- [ ] Application list and tracking timeline: submitted → verification → review → approved/rejected.

### 10. Wealth `/portal/wealth` — PARTIAL (A)

- [x] Fixed deposit, mutual fund, insurance, stock and bond categories.
- [x] Details notice and comparison of up to three categories.
- [x] Risk and illustrative minimum comparison without fabricated return promises.
- [ ] Actual product catalogue, provider details, fees, returns and disclosures from API.
- [ ] Investment portfolio, holdings and performance records.
- [ ] Product-specific invest/purchase journey and confirmations.

### 11. Recommendations `/portal/recommendations` — PARTIAL (A)

- [x] Dedicated For You page and dashboard entry point.
- [x] Sample savings, investment, loan and insurance suggestions with working links.
- [ ] Real recommendation feed, why-recommended explanation, dismiss/feedback and consent.

### 12. Spending analytics `/portal/analytics` — PARTIAL (A)

- [x] Sample income/expense/savings totals, six-month comparison, category breakdown.
- [x] Static insights, readable legends and chart text descriptions.
- [ ] Date/account/category selection, real aggregation and generated insights.
- [ ] Engagement instrumentation using agreed privacy/event contracts.

### 13. AI assistant (global customer shell) — PARTIAL (A)

- [x] Floating toggle, responsive conversation panel, prompts, local history, text input and new conversation.
- [x] Deterministic sample responses about spending, loans and investments; labelled as scripted.
- [ ] Real AI conversation API and streaming/typing/cancel/error/retry states.
- [ ] Persistent conversations, contextual action buttons and authorization boundaries.

### 14. Notifications `/portal/notifications` — PARTIAL (A)

- [x] Sample suspicious transaction, sign-in, transfer and loan events.
- [x] Mark-all-read and recognize/report transaction preview responses.
- [ ] Live unread counts, individual read state, notification pagination and persistence.
- [ ] Real fraud acknowledgement/report workflow and durable case reference.

### 15. Profile & settings `/portal/settings` — PARTIAL (A)

- [x] Profile/contact preview with validation and save feedback.
- [x] Notification preference controls in local page state.
- [ ] Durable profile/contact updates and re-verification.
- [ ] Change password, MFA enrolment, recovery codes and account preferences.
- [ ] Active sessions/devices and revoke session workflow.
- [ ] Production logout and security preference enforcement.

## Internal banking portal — Person 1 frontend implemented

The following scoped interfaces are complete using shared fictional records. Admin login opens this workspace; backend authentication, protected routes, RBAC and live data remain TODO. The separate admin layout includes responsive navigation and customer search.

- [x] `/admin/dashboard`: six KPI cards, recent alerts, behaviour charts and activity links.
- [x] `/admin/customers`: name/ID/email search, risk/alert/segment filters, sorting, pagination and detail links.
- [x] `/admin/customers/[id]`: overview, masked accounts, transactions, spending/income trends, read-only products, risk, incident history, behaviour and a filtered analytics link.
- [x] `/admin/analytics`: 7/30/90-day and custom periods; segment/product/customer filters; segmentation, spending, income, affinity, page visits, clickstream, session and customer summaries.
- [x] Loading, retry, empty and unknown-customer states; desktop, tablet and mobile layouts.
- [x] Customer directory shows active account counts rather than combined balances; balance sorting and the directory balance column are removed. Account balances remain within individual customer account details. Admin sidebar has no public-home redirect.
- [x] Behaviour analytics shows each customer's top spending category for the selected period rather than their monthly spending amount. Removed the average income amount and the Income trend / Spending trend charts; aggregate income bands and spending categories remain.
- [ ] Live admin APIs and employee authentication/authorization.

`frontend/src/lib/admin/service.ts` is the data integration seam. Types, fixtures and derived metrics live beside it. Continue other modules below separately; this delivery does not implement operational actions or investigation workflows.

| Module | Proposed routes | Full checklist |
| --- | --- | --- |
| Employee authentication | `/admin/login`, `/admin/mfa`, `/admin/forgot-password` | Employee email/ID, password, MFA, reset, expiry, failed login, role-aware redirect |
| Dashboard | `/admin/dashboard` | Customer count, active/critical fraud, high-risk customers, investigations, transaction volume, applications, trend charts, recent alerts |
| Fraud monitoring | `/admin/fraud` | Alert totals, risk scores, sortable table, risk/date/customer/amount/type/status filters, pagination, empty/error/loading states |
| Fraud investigation | `/admin/fraud/[id]` | Customer + transaction details, why flagged, history, login activity, event timeline, mark safe, escalate, block/flag, resolve; confirm impactful actions |
| Customer management | `/admin/customers`, `/admin/customers/[id]` | Search by ID/name/account/email; profile, accounts, balances, transactions, loans, investments, risk, alerts, recommendations and behavior insights |
| Behavioral analytics | `/admin/analytics` | Customer segments, spending patterns, product affinity, engagement, active users, session duration, page views, interests, clicks and conversions |
| Loan management | `/admin/loans`, `/admin/loans/[id]` | Applications, filter/search, applicant details, eligibility, financials, amount, documents and status; actions per permitted role |
| Products/recommendations | `/admin/products`, `/admin/recommendations` | Product catalogue and agreed management actions; recommended → clicked → applied analytics |
| Compliance & risk | `/admin/compliance` | Compliance alerts, severity, exception management and regulatory monitoring |
| Audit log | `/admin/audit` | Actor, action, resource, timestamp, search/date/resource filters, pagination and authorized export |
| Security monitoring | `/admin/security` | Active alerts, high-risk customers, login anomalies, fraud events and open investigations |
| Administration | `/admin/users`, `/admin/roles`, `/admin/configuration` | Users, roles, permissions, transaction limits, application settings, notification settings; review/confirmation and audit results |

### Role policy to agree with the backend team

- CUSTOMER: customer portal and own records only.
- RELATIONSHIP_MANAGER: authorized customer/relationship and product insights.
- FRAUD_ANALYST: authorized fraud monitoring and investigations.
- COMPLIANCE_OFFICER: authorized compliance, exceptions and audit.
- ADMIN: explicitly granted operational/configuration permissions.

This is a proposed allocation, not an implemented permission matrix. Get domain-owner agreement. Frontend route checks and permission-aware rendering must be accompanied by server enforcement; hiding a button is not access control.

## Integration handoff

Repository inspection found real `POST /api/v1/auth/register`, `POST /api/v1/auth/login` and `GET /api/v1/me` foundations. Registration accepts email, password, first_name, last_name and optional phone. Login accepts email and password and returns a bearer token plus role/user ID. Customer accounts and transfers inspected are placeholder responses. Do not assume other endpoint response shapes are final.

1. Agree API contracts with backend owners; follow the repository rule requiring PR review for shared schema/response changes.
2. Introduce an API/service layer outside UI components, keeping sample fixtures separate.
3. Implement secure sessions and server checks before placing real data behind portal routes.
4. Replace fixtures module by module; add loading/error/empty/retry states as each module becomes live.
5. Reconcile amounts, payees, receipts, schedules, notifications and analytics against the same data source.
6. Remove sample labels only for capabilities that actually call and validate a live service.

## Files and collaboration boundaries

- Landing: `frontend/src/app/page.tsx`.
- Auth previews: `frontend/src/components/auth-page.tsx` and corresponding routes.
- Customer shell + assistant: `frontend/src/components/portal-shell.tsx`.
- Customer page implementations: `frontend/src/components/customer-pages.tsx`; route registry in `src/app/portal/[section]/page.tsx`.
- Fixtures: `frontend/src/lib/sample-data.ts`.
- Shared tokens/layouts: `frontend/src/app/globals.css`; shared primitives: `src/components/ui.tsx`.
- Admin workspace: `frontend/src/app/admin/(workspace)/`; shared admin components: `frontend/src/components/admin/`; data contracts/service: `frontend/src/lib/admin/`.
- Before independently extending a customer module, move that component into `src/components/customer/<module>.tsx` in a small agreed refactor. This prevents two people editing the same large starter file.
- Never commit credentials, `.env`, `.next`, `node_modules`, caches or generated reports.

## Definition of frontend done

- [ ] Scope and owner agreed; intended route works through navigation and direct refresh.
- [ ] Every visible action works or honestly communicates its unavailable state.
- [ ] Relevant success, empty, validation, loading and failure states implemented.
- [ ] Keyboard, mobile width, labels, visible focus and readable contrast checked.
- [ ] `npm run typecheck` and `npm run build` pass.
- [ ] Relevant interaction checks pass; no browser console errors.
- [ ] API integration is separately recorded from sample UI completion.
- [ ] Update this tracker and shared design notes in the same change.

## Change log

### Person 1 admin frontend — 2026-10-05

- Production build and TypeScript validation passed.
- Playwright: **19/19 passed**, including five admin checks and fourteen customer checks.
- Verified desktop, tablet and mobile navigation; combined filters, sorting, pagination, details, custom periods, unknown customers and page overflow.
- Completed interfaces use shared fixtures. Live APIs, authentication, RBAC and operational modules remain pending.

### Verification for the initial frontend delivery

- Production build: passed; 20 static pages generated by Next.js 16.3.6.
- TypeScript check: passed.
- Formatting check: passed.
- Playwright: **14/14 passed** against the production build in headless Microsoft Edge.
- Checked desktop at 1440 × 1000 and mobile at 390 × 844. Reviewed landing/dashboard screenshots; corrected mobile illustration overflow.
- Interaction coverage: navigation, transaction filters/empty state, transfer balance validation and paise preservation, invalid/valid sample OTP, bill shortcut, payee add/delete confirmation, custom statement period, zero-interest EMI, comparison selection limit, scripted assistant, sample login and unknown-route handling.
- Direct mobile-route checks cover schedules, analytics, recommendations, notifications and settings. These checks do not imply complete end-to-end coverage for every future feature.
- Dependency installation audit: zero known vulnerabilities reported after updating dependencies.
- Not performed: live backend integration, real authentication/payment/security testing, cross-browser Safari/Firefox testing, full accessibility audit or official PDF generation.
- The in-app browser connection was unavailable; local headless Edge was used for browser verification.

| Date | Developer | Change |
| --- | --- | --- |
| 2026-09-26 | A / initial implementation | Created frontend foundation, landing, auth previews, customer sample modules, shared feature tracker and design system guide. No internal pages or real banking integrations claimed complete. |
