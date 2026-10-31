# Credora- Personal Banking Intelligence Platform

Industry-aligned final-year software engineering capstone project.

## Platform overview

- Microservices architecture behind an nginx API gateway
- FastAPI customer and admin services
- Next.js frontend for the customer portal and the internal banking workspace
- PostgreSQL (Supabase) via SQLAlchemy + asyncpg, Alembic migrations
- JWT authentication with role-based access control
- Docker Compose for the full stack, migrations and data seeding
- OpenAPI/Swagger documentation per service

## Architecture

| Container | Responsibility | Host port |
| --- | --- | --- |
| `gateway` (nginx) | Single entry point; routes requests to the services | `8080` |
| `frontend` | Next.js UI (`/`, `/portal/*`, `/admin/*`) | via gateway |
| `customer-service` | Authentication, `/me`, customer profile, accounts, transactions, payees, transfers, bills, loans, investments, insurance, recommendations, AI assistant | `8001` (Swagger `/docs`) |
| `admin-service` | Internal analytics, fraud investigation and compliance (`/analytics/*`, `/fraud/*`, `/compliance/*`) | `8002` (Swagger `/docs`) |

Gateway routing (`gateway/nginx.conf`): `/api/v1/analytics|fraud|compliance/*` → admin-service, all other `/api/v1/*` → customer-service, everything else → frontend. Both portals sign in through `POST /api/v1/auth/login`.

Architecture details and the full API-to-service mapping: [docs/architecture/MICROSERVICES_MIGRATION_PLAN.md](docs/architecture/MICROSERVICES_MIGRATION_PLAN.md).

## Running the platform

Prerequisites: Docker Desktop and a repo-root `.env` file (`DATABASE_URL` for Supabase, `JWT_SECRET_KEY`, `GROQ_API_KEY`). Use `backend/.env.example` as the template if the file does not exist.

```powershell
docker compose up --build -d
```

Open `http://localhost:8080`.

A local Postgres service is included in `docker-compose.yml` but commented out; the comments there explain how to enable it.

### Database migrations

```powershell
docker compose --profile setup run --rm migrate
```

Runs `alembic upgrade heads`. The migration history has two branches from `e5f6a7b8c9d0`, so `heads` (plural) is required. Do not create tables manually in the Supabase dashboard; the migration files are the source of truth.

### Seed data

```powershell
docker compose --profile seed run --rm seed
```

Runs migrations, then `python -m scripts.seed` (demo users for every role with password `PBIP@Demo123`, products, billers), then `python -m data.generators.generate` (synthetic customers, transactions, behaviour events, fraud scenarios, risk profiles). The job is idempotent. It writes to the shared Supabase database, so the data is visible to the whole team.

## Backend development

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
```

Tests run against an in-memory SQLite database and never touch Supabase. `tests/test_service_split.py` verifies that the customer and admin services together expose the complete API and that the gateway routes every endpoint to the service that serves it.

When adding an endpoint, register its router in `app/customer_main.py` or `app/admin_main.py`. A new admin route prefix must also be added to the admin location in `gateway/nginx.conf`.

## Authentication

Database-backed registration and login, bcrypt password hashing, JWT access tokens, current-user lookup, role-based access control, audit logging and login security events.

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/me`

Supported roles: `CUSTOMER`, `RELATIONSHIP_MANAGER`, `FRAUD_ANALYST`, `COMPLIANCE_OFFICER`, `ADMIN`.

Never commit `.env` or production credentials.

## Team rule

The database schema and API contracts are shared contracts. Changes to shared models or API response shapes require a PR and review from the relevant domain owners.

## Frontend development

```powershell
cd frontend
npm install
npm run dev
```

The frontend calls the API at `NEXT_PUBLIC_API_URL`. Set it to `http://localhost:8080/api/v1` to use the gateway. In Docker the value is set at build time through the `frontend` build arg in `docker-compose.yml`.

## Frontend routes

| Page | Route |
| --- | --- |
| Landing | `/` |
| Customer login / sign-up | `/login`, `/register` |
| Admin login | `/admin/login` |
| Admin dashboard | `/admin/dashboard` |
| Customer directory / details | `/admin/customers`, `/admin/customers/[id]` |
| Admin behaviour analytics | `/admin/analytics` |
| Password recovery / session expired | `/forgot-password`, `/session-expired` |
| Customer dashboard | `/portal/dashboard` |
| Accounts | `/portal/accounts` |
| Transfers / bill payments | `/portal/payments`, `/portal/payments?tab=bills` |
| Payees / scheduled payments | `/portal/payees`, `/portal/scheduled` |
| Statements | `/portal/statements` |
| Loans / investments | `/portal/loans`, `/portal/wealth` |
| Analytics / recommendations | `/portal/analytics`, `/portal/recommendations` |
| Notifications / settings | `/portal/notifications`, `/portal/settings` |
