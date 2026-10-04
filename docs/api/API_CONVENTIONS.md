# PBIP API Conventions

## Base path

`/api/v1`

## Response style

JSON responses with stable field names. IDs are UUIDs and timestamps are ISO-8601.

## Domain prefixes

- `/auth`
- `/customers`
- `/accounts`
- `/transactions`
- `/payees`
- `/transfers`
- `/bills`
- `/loans`
- `/investments`
- `/recommendations`
- `/fraud`
- `/analytics`
- `/compliance`
- `/notifications`
- `/ai`

## Rules

- Authentication uses Bearer JWT.
- Domain authorization is enforced server-side.
- Frontend must not depend on database structure directly.
- AI tools must call backend APIs, not arbitrary SQL.
- Breaking API changes require a version or an explicit team-approved migration.

## Domain API references

- [Customer Banking API](customer/README.md): customers, accounts, transactions, payees, transfers, bills, loans, investments, insurance, recommendations
