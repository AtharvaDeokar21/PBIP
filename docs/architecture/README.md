# PBIP Architecture

PBIP uses a modular monolith architecture initially.

Frontend clients communicate with versioned FastAPI REST endpoints. Domain services use SQLAlchemy to access Supabase PostgreSQL. AI requests are mediated through backend services and APIs rather than granting the LLM direct database access.

See the project use-case document for the business scope and required engineering outcomes.
