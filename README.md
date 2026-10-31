# Credora- Personal Banking Intelligence Platform

Industry-aligned final-year software engineering capstone project.

## Current foundation

- FastAPI backend
- PostgreSQL/Supabase connectivity via SQLAlchemy + asyncpg
- Alembic migrations
- JWT/RBAC foundation
- Core banking, product, intelligence, fraud, system and AI persistence models
- Dockerized backend
- OpenAPI/Swagger documentation

## Architecture (microservices)

The app runs as separate containers behind an nginx API gateway. Both backend services run the same `backend/app` code and share one PostgreSQL database (`public` schema), so every API behaves exactly as it did in the monolith.

| Container | What it serves | Host port |
| --- | --- | --- |
| `gateway` (nginx) | Single entry point — open the app here | `8080` |
| `frontend` | Next.js UI (`/`, `/portal/*`, `/admin/*`) | via gateway |
| `customer-service` | `app.customer_main` — auth (shared login), `/me`, customers, accounts, transactions, payees, transfers, bills, loans, investments, insurance, recommendations, AI | `8001` (Swagger `/docs`) |
| `admin-service` | `app.admin_main` — `/analytics/*`, `/fraud/*`, `/compliance/*` | `8002` (Swagger `/docs`) |

Gateway routing (`gateway/nginx.conf`): `/api/v1/analytics|fraud|compliance/*` → admin-service, every other `/api/v1/*` → customer-service, everything else → frontend. Login for both portals stays `POST /api/v1/auth/login`. `backend/tests/test_service_split.py` checks that the two services together expose exactly the monolith's routes and that the gateway sends each route to the right service.

Full plan and API inventory: [docs/architecture/MICROSERVICES_MIGRATION_PLAN.md](docs/architecture/MICROSERVICES_MIGRATION_PLAN.md).

### Run with Docker

```powershell
copy backend\.env.example .env   # repo-root .env: Supabase DATABASE_URL, JWT_SECRET_KEY, GROQ_API_KEY
docker compose up --build -d
```

Open `http://localhost:8080`.

All backend containers use the Supabase database from `DATABASE_URL` in the repo-root `.env` (Docker reads it via `env_file`; skip the copy step if it already exists). A local Postgres service is included in `docker-compose.yml` but commented out; the comments there explain how to switch to it.

### Seed data

```powershell
docker compose --profile seed run --rm seed
```

This runs `alembic upgrade head`, then `python -m scripts.seed` (demo users for every role, password `PBIP@Demo123`, plus products and billers), then `python -m data.generators.generate` (synthetic customers, transactions, behaviour, fraud, risk profiles). It is safe to re-run (existing demo/synthetic data is detected and skipped). It writes to the shared Supabase database, so everyone on the team sees the data.

Migrations only: `docker compose --profile setup run --rm migrate`.
Old single backend (fallback): `docker compose --profile monolith up backend` → `http://localhost:8000`.

## Backend setup

```powershell
cd backend
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Fill `DATABASE_URL` and `JWT_SECRET_KEY` in `.env`.

Run:

```powershell
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs`.

## Database migrations

From `backend/`:

```powershell
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

The initial migration already exists in this repository; for setup, run only `alembic upgrade head`. Generate a new revision when intentionally changing the schema.

Do not manually create production tables in the Supabase dashboard. The migration files are the source of truth.

## Team rule

The database schema and API contracts are shared contracts. Changes to shared models or API response shapes require a PR and review from the relevant domain owners.

## Authentication foundation

The backend now includes database-backed customer registration and login, bcrypt password hashing, JWT access tokens, current-user lookup, role-based access control, audit logging, and login security events.

Development endpoints:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/me`

Supported roles:

- `CUSTOMER`
- `RELATIONSHIP_MANAGER`
- `FRAUD_ANALYST`
- `COMPLIANCE_OFFICER`
- `ADMIN`

Never commit `.env` or production credentials.

## Auth v0.2 verification

From `backend/`:

```powershell
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --reload
```

Then use Swagger at `http://127.0.0.1:8000/docs`.

### Register

`POST /api/v1/auth/register`

```json
{
  "email": "customer@example.com",
  "password": "StrongPassword123!",
  "first_name": "Aarav",
  "last_name": "Shah"
}
```

### Login

`POST /api/v1/auth/login`

Use the returned bearer token with `GET /api/v1/me`.

Authentication is database-backed. Successful and failed logins create security events, and successful logins create an audit log entry.

## Frontend setup

From the repository root:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:3000`.

For a production build:

```powershell
npm run build
npm start
```

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

The frontend currently uses sample data. Customer and admin login open their respective workspaces without backend authentication; live integration is pending.
