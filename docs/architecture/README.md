# PBIP Architecture

PBIP runs as microservices behind an nginx API gateway: frontend (Next.js), customer-service and admin-service (FastAPI, same `backend/app` codebase, separate entrypoints), sharing one PostgreSQL database. See [MICROSERVICES_MIGRATION_PLAN.md](MICROSERVICES_MIGRATION_PLAN.md).

Frontend clients communicate with versioned FastAPI REST endpoints. Domain services use SQLAlchemy to access Supabase PostgreSQL. AI requests are mediated through backend services and APIs rather than granting the LLM direct database access.

See the project use-case document for the business scope and required engineering outcomes.
