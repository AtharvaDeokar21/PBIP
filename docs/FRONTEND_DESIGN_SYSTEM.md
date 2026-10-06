# Credora frontend design system

Use this document when building additional customer or internal pages, including as context for an AI coding tool. The source of truth is `frontend/src/app/globals.css`.

## Visual direction

Professional personal banking: calm, clear, spacious and approachable. Purple and white are inspired by the requested SBI YONO color direction, but this is an independent Credora design. Do not use SBI/YONO logos, claim affiliation, or describe these tokens as verified official SBI colors.

Use Credora's lowercase `credora.` wordmark with the Lucide Landmark icon in a purple rounded square. The trailing dot is muted pink. Do not generate a competing logo or icon system.

## Colors

| Token | Hex | Intended use |
| --- | --- | --- |
| `--purple` | `#7134A3` | Primary buttons, active navigation, links, key chart series |
| `--purple-dark` | `#4B1C72` | Brand text, deep background, high emphasis |
| `--purple-hover` | `#5B2688` | Primary-button hover |
| `--lavender` | `#F1E9F8` | Icon backgrounds, selected controls, soft callouts |
| `--pink` | `#D06BA5` | Small brand/notification accents only |
| `--ink` | `#292332` | Primary text and amounts |
| `--muted` | `#797281` | Supporting text; check contrast before small text on tinted surfaces |
| `--line` | `#EAE6EE` | Borders, separators, table rules |
| `--canvas` | `#F8F7FA` | Customer app background |
| `--white` | `#FFFFFF` | Cards, forms, landing background |
| `--green` | `#278264` | Credits, positive results and healthy status |
| `--green-bg` | `#EAF5EF` | Success badges/backgrounds |
| `--danger` | `#B23848` | Destructive actions and validation errors |
| `--peach` | `#FFF0E7` | Gentle attention surfaces; use text and icon too |

Chart palette: `#7134A3`, `#A371CB`, `#D0B3E5`, `#EBE0F3`. Income is primary purple; expense comparison is `#D6BDE7`. Never rely on color alone for status or chart meaning. Include labels, values, legends and accessible descriptions. Verify contrast for final production content; tiny decorative labels are not a substitute for readable financial details.

## Typography

- Base: `Arial, Helvetica, sans-serif`, local/system fonts; no third-party font request needed.
- Editorial accent: Georgia italic for the landing hero's “personal.” and a few marketing accents only.
- Landing hero: 46–65 px desktop, approximately 49 px mobile, regular/medium weight, tight letter spacing.
- Marketing section headings: 30–37 px. Customer page titles: 25–27 px. Card headings: 15–20 px.
- Base body is 14 px. The initial dashboard uses compact secondary/table text; when building denser admin pages, prefer 12–14 px table/body text rather than shrinking content to fit.
- Eyebrows: uppercase, small, 1.3–1.65 px letter spacing. Use sparingly.
- INR currency: `Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' })`. Show decimals where needed, including payment review/receipts. Display masks for account numbers.

## Layout

- Landing content maximum width 1200 px; white background, generous vertical rhythm, soft custom CSS financial illustrations.
- Customer desktop: fixed white left sidebar (238 px, shrinking at intermediate widths); header with breadcrumb and profile; lavender sample banner; off-white canvas.
- Main page: title/description first, then overview cards, actions, detail content.
- Reuse `.panel`, `.page-heading`, `.section-heading`, `.dashboard-columns`, `.overview-grid`, `.button`, `.text-link`, `.icon-tile`, `.status`, `.notice`, `.form-error` and `.empty-state`.
- Card radius: 13–16 px. Button/input radius: 7–8 px. Borders are soft and shadows restrained.
- Typical card padding: 21–28 px. Typical gaps: 18–24 px. Group related controls instead of scattering actions.
- Breakpoints in existing CSS: 1150, 900, 680 and 370 px. At 680 px the sidebar becomes a toggled drawer; customer grids collapse. Wide data tables scroll horizontally.
- Admin pages should share color/typography/components, with more room for tables and clear role context. Do not reuse customer sample balances as operational metrics.

## Components and interaction

- Primary action: purple filled button, white text, Lucide arrow where useful.
- Secondary action: white background, neutral border, dark text.
- Tertiary action: purple text link with an arrow.
- Destructive action: red text/icon plus a confirmation step for consequential changes.
- Use Lucide icons from `lucide-react`, generally 16–24 px. Avoid mixing icon families or using emoji as controls.
- Every input has a visible label. Use `aria-label` for icon-only controls.
- Always include clear empty states and meaningful validation. Live features also require loading, error and retry states.
- Selected links use `aria-current`; toggles use `aria-expanded` or `aria-pressed` as appropriate.
- Retain visible focus outlines and skip-to-content link. Respect reduced-motion preference.
- Keep flows reviewable: input → review → verification → processing → outcome. Never claim a payment succeeded without server confirmation. The current sample explicitly says no money moved.
- Date, amount and account details need to remain visible during review. Never round payment amounts to whole rupees.
- Do not request real credentials in sample forms. Do not silently store financial information in local storage.
- No invented regulatory badges, insurance claims, bank partnerships, guaranteed returns, live AI claims or fake security certifications.

## Content voice

Warm but precise. Short phrases such as “Your money at a glance” or “One last look” are welcome, but an error must clearly explain what to change. Make operational states unambiguous: scheduled, pending, completed, failed, cancelled. Use “sample”, “illustrative” or “sample” wherever data or actions are simulated.

## Reusable AI implementation prompt

> Build the [FEATURE NAME] page for Credora using the existing Next.js App Router, TypeScript and Tailwind foundation. First read docs/FRONTEND_FEATURE_TRACKER.md and inspect existing shared components and globals.css. Follow docs/FRONTEND_DESIGN_SYSTEM.md. Reuse the Credora purple (#7134A3), deep purple (#4B1C72), lavender (#F1E9F8), white cards, off-white canvas (#F8F7FA), ink (#292332) and muted text (#797281). Use Lucide icons, the existing sidebar/header, 13–16px card radii, restrained borders/shadows and responsive grids. Maintain professional banking hierarchy, labelled inputs, readable monetary values, keyboard access and focus outlines. Do not add SBI branding. Implement all visible actions and relevant validation/empty/loading/error states. Clearly distinguish sample from live actions. Do not change shared API contracts without review. Claim the feature row, avoid duplicating completed modules, and mark actual completion plus remaining integration work in the tracker after checking the build.

## Internal workspace components

Admin pages reuse Credora colours and Lucide icons through `frontend/src/components/admin/ui.tsx`. The isolated workspace styles live in `frontend/src/app/admin/(workspace)/admin.css`. Reuse its KPI cards, chart panels, risk/status badges, filters, table wrappers, pagination and loading/error/empty states. Keep customer details and products read-only in the Person 1 scope. Customer links use stable IDs, and analytics links preserve customer filters.

## Review before handing off

Check desktop and narrow-mobile layouts, sidebar behavior, direct route refresh, no accidental horizontal page overflow, input validation, control labels, action targets and honest outcome messages. Screenshot review and contrast/accessibility verification remain necessary before production sign-off.
