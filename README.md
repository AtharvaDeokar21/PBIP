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
| Password recovery / session expired | `/forgot-password`, `/session-expired` |
| Customer dashboard | `/portal/dashboard` |
| Accounts | `/portal/accounts` |
| Transfers / bill payments | `/portal/payments`, `/portal/payments?tab=bills` |
| Payees / scheduled payments | `/portal/payees`, `/portal/scheduled` |
| Statements | `/portal/statements` |
| Loans / investments | `/portal/loans`, `/portal/wealth` |
| Analytics / recommendations | `/portal/analytics`, `/portal/recommendations` |
| Notifications / settings | `/portal/notifications`, `/portal/settings` |

The frontend currently uses sample data. Customer login opens the workspace without backend authentication; live banking integration is pending.
