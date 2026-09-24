# PBIP - Personal Banking Intelligence Platform

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

```bash
cd backend
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Fill `DATABASE_URL` and `JWT_SECRET_KEY` in `.env`.

Run:

```bash
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs`.

## Database migrations

From `backend/`:

```bash
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

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

```bash
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
