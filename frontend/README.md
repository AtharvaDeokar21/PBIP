# Credora Frontend

Next.js App Router + TypeScript + Tailwind CSS customer frontend. Purple-and-white Credora branding, responsive landing page and interactive customer preview. No real banking operations or authentication are performed.

## Run locally

```powershell
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:3000. Landing-page cards and exploration links lead to customer sign-up. The sample customer workspace is available directly at `/portal/dashboard` during frontend development. No environment variables, database or bank credentials are needed.

```powershell
npm run typecheck
npm run build
npm start
```

## Team documents

- [Feature tracker and ownership](../docs/FRONTEND_FEATURE_TRACKER.md): implemented screens, partial flows, remaining customer features, complete internal-portal backlog and integration handoff.
- [Design system and reusable AI prompt](../docs/FRONTEND_DESIGN_SYSTEM.md): colors, typography, components, layouts and collaboration rules.

Update the feature tracker whenever a page or flow changes. UI DONE does not mean backend integration is complete.

## Main routes

Landing `/`; customer login `/login`, customer sign-up `/register`, and separate admin login `/admin/login`. Supporting routes: `/forgot-password`, `/session-expired`. Customer login opens the public sample workspace without sending credentials or creating an authenticated session. Sign-up, admin login and password recovery remain unavailable until backend integration.

Customer pages under `/portal/`: `dashboard`, `accounts`, `payments`, `payees`, `statements`, `scheduled`, `loans`, `wealth`, `analytics`, `recommendations`, `notifications`, `settings`.

Payments supports `?tab=bills`. Sample OTP: **123456**. Account/transfer fixtures are illustrative. Payee, schedule, profile, notification and chat changes are page-local previews and reset when unmounted. Statement printing uses your browser's Print / Save as PDF; official generated PDFs are pending.

## Browser checks

After building, run `npm run test:e2e`. Tests start the production server automatically and cover the main sample flows and mobile layouts. Install the test browser once with `npx playwright install chromium`, or use an installed Edge browser on Windows:

```powershell
$env:CREDORA_BROWSER_CHANNEL = 'msedge'
npm run test:e2e
```

Screenshots are generated under the ignored `test-results/` folder. `npm run format:check` checks source formatting; `npm run format` applies it.

## Source structure

- `src/app/page.tsx`: marketing landing page.
- `src/app/portal/[section]/page.tsx`: allowed customer route registry; unknown sections return 404.
- `src/components/customer-pages.tsx`: initial customer page implementations. Split modules into separate files before parallel editing.
- `src/components/portal-shell.tsx`: customer navigation and scripted assistant.
- `src/components/auth-page.tsx`: sample-only authentication forms.
- `src/components/ui.tsx`: shared visual primitives.
- `src/lib/sample-data.ts`: fixtures; replace through an agreed service layer during integration.
- `src/app/globals.css`: shared tokens, styling, responsive and print layouts.

## Integration boundary

Auth endpoints exist in the FastAPI backend, but this frontend does not call them yet. It has no production session, protected routes or RBAC. Account and transfer endpoints inspected in this repository are placeholders. Coordinate contracts and security with backend owners before adding real banking data. Admin login UI exists; admin operational pages remain available for the other developer.
