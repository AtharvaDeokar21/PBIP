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
