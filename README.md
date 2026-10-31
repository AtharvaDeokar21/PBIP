# Credora- Personal Banking Intelligence Platform

Industry-aligned final-year software engineering capstone project.

## Platform overview

- Microservices architecture behind an nginx API gateway
- FastAPI customer and admin services, Next.js frontend
- PostgreSQL (Supabase) via SQLAlchemy + asyncpg, Alembic migrations
- JWT authentication with role-based access control
- CI/CD with Jenkins (pipeline as code) and SonarQube static analysis
- Observability: Prometheus (metrics), Loki + Grafana Alloy (logs), Grafana (provisioned dashboards)
- Structured JSON logging with request correlation across gateway and services
- Docker Compose for the application, observability and CI stacks

## URLs and ports

| Service | URL | Login |
| --- | --- | --- |
| Credora app (gateway) | http://localhost:8080 | — |
| Customer portal | http://localhost:8080/login | Customer account (seed: `customer@pbip.demo` / `PBIP@Demo123`) |
| Internal banking portal | http://localhost:8080/admin/login | Staff account (seed: `admin@pbip.demo` / `PBIP@Demo123`) |
| Customer service API docs | http://localhost:8001/docs | — |
| Admin service API docs | http://localhost:8002/docs | — |
| Grafana | http://localhost:3001 | `GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD` (default `admin` / `admin`) |
| Prometheus | http://localhost:9090 — targets `/targets`, alerts `/alerts` | — |
| Loki | http://localhost:3100/ready (API only; browse logs in Grafana) | — |
| Grafana Alloy | http://localhost:12345 | — |
| Jenkins | http://localhost:8081 | `JENKINS_ADMIN_USER` / `JENKINS_ADMIN_PASSWORD` (default `admin` / `admin`) |
| SonarQube | http://localhost:9000 — project `/dashboard?id=credora` | `admin` / `SONAR_ADMIN_PASSWORD` (default `Credora@Sonar1`) |

Internal only (not published on the host): frontend `3000`, service containers `8000`, nginx `stub_status` `8081`, nginx exporter `9113`.

## Architecture

| Container | Responsibility | Host port |
| --- | --- | --- |
| `gateway` (nginx) | Single entry point; routes requests to the services | `8080` |
| `frontend` | Next.js UI (`/`, `/portal/*`, `/admin/*`) | via gateway |
| `customer-service` | Authentication, `/me`, customer profile, accounts, transactions, payees, transfers, bills, loans, investments, insurance, recommendations, AI assistant | `8001` |
| `admin-service` | Internal analytics, fraud investigation and compliance (`/analytics/*`, `/fraud/*`, `/compliance/*`) | `8002` |
| `prometheus`, `loki`, `alloy`, `grafana`, `nginx-exporter` | Observability (always on) | see above |

Gateway routing (`gateway/nginx.conf`): `/api/v1/analytics|fraud|compliance/*` → admin-service, all other `/api/v1/*` → customer-service, everything else → frontend. Both portals sign in through `POST /api/v1/auth/login`.

Architecture details and the API-to-service mapping: [docs/architecture/MICROSERVICES_MIGRATION_PLAN.md](docs/architecture/MICROSERVICES_MIGRATION_PLAN.md). CI/CD and observability design: [docs/architecture/CICD_OBSERVABILITY_PLAN.md](docs/architecture/CICD_OBSERVABILITY_PLAN.md).

## Configuration

All stacks read the repository-root `.env` (never committed). Create it from the template:

```powershell
copy .env.example .env
```

| Key | Purpose |
| --- | --- |
| `DATABASE_URL` | Supabase PostgreSQL connection (asyncpg) |
| `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` | Token signing |
| `GROQ_API_KEY`, `GROQ_MODEL` | AI assistant |
| `LOG_LEVEL` | Service log level (default `INFO`) |
| `GRAFANA_ADMIN_USER`, `GRAFANA_ADMIN_PASSWORD` | Grafana login |
| `JENKINS_ADMIN_USER`, `JENKINS_ADMIN_PASSWORD` | Jenkins login |
| `SONAR_ADMIN_PASSWORD` | SonarQube admin password (at least 12 characters with upper case, lower case, a digit and a special character) |

Optional keys fall back to the defaults shown in the URLs table.

## Running the platform

Prerequisites: Docker Desktop (8 GB memory or more when the CI stack also runs) and the root `.env`.

```powershell
docker compose up --build -d
```

Starts the gateway, frontend, both services and the observability stack. Open http://localhost:8080.

```powershell
docker compose ps        # status and health
docker compose down      # stop (volumes are kept)
```

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

## CI/CD (Jenkins + SonarQube)

### Start the CI stack

```powershell
docker compose -f ci/docker-compose.yml up -d --build
```

Everything is provisioned automatically on start — no setup wizard, no copied tokens:

| Component | Provisioned |
| --- | --- |
| SonarQube | `sonar-init` changes the default admin password, creates project `credora`, assigns the *Sonar way* quality gate, sets the new-code definition, registers the Jenkins webhook and generates the analysis token. |
| Jenkins | Plugins pre-installed; admin user, credentials (`credora-env` from the root `.env`, `sonar-token` from `sonar-init`), SonarQube server and the `credora` pipeline job created by configuration as code (`ci/jenkins/casc.yaml`). |

SonarQube needs 1–2 minutes to start; Jenkins starts after provisioning has finished.

```powershell
docker compose -f ci/docker-compose.yml ps     # status
docker compose -f ci/docker-compose.yml down   # stop (volumes are kept)
```

### Pipeline

Job `credora` builds `https://github.com/AtharvaDeokar21/PBIP` branch `feature/cicd` using the root `Jenkinsfile`. The branch is polled every 2 minutes: the first build starts automatically shortly after Jenkins comes up, and **every push to `feature/cicd` triggers a build**. *Build with Parameters* runs it manually.

| Stage | What it does |
| --- | --- |
| Checkout | Clean workspace, check out the branch |
| Prepare | Write `.env` from the Jenkins credential, validate compose files |
| Test → Backend tests | `pytest` with JUnit and coverage reports, Ruff report (`python:3.12-slim`) |
| Test → Frontend checks | `npm ci` and TypeScript type check (`node:22-bookworm-slim`) |
| SonarQube analysis | Scans the Python and TypeScript/JavaScript sources and imports coverage, test and Ruff reports |
| Quality gate | Waits for the SonarQube result; **a failed gate aborts the pipeline** |
| Build images | Builds all application and observability images, tagged `<build>-<commit>` |
| Deploy | `docker compose up --wait`; succeeds when every container is healthy |
| Seed database | Migrations + seed + synthetic data; parameter `SEED_DB` (default on) |

Test results and coverage appear on the build page; reports are archived as build artifacts. The pipeline deploys to the same Docker engine as local development and replaces the running `credora` stack.

### Static analysis

The SonarQube project `credora` (http://localhost:9000/dashboard?id=credora) analyses `backend/app`, `backend/scripts` (Python) and `frontend/src` (TypeScript/JavaScript), with backend coverage, test results and Ruff findings imported. Configuration: `sonar-project.properties`. The *Sonar way* gate evaluates new code (no new issues, reviewed security hotspots, at least 80 % coverage and at most 3 % duplication on new code); the first analysis establishes the baseline.

## Observability

| Signal | Collected by | Where to look |
| --- | --- | --- |
| Metrics | Prometheus scrapes `/metrics` of both services, the nginx exporter, Loki, Alloy, Grafana and Jenkins every 15 s | Grafana dashboards, http://localhost:9090 |
| Logs | Grafana Alloy reads every Credora container's stdout through the Docker API and ships it to Loki | Grafana → *Credora · Logs*, or *Explore* with the Loki datasource |
| Alerts | Prometheus rules: service down, 5xx ratio above 5 %, p95 latency above 1 s, last Jenkins build failed | http://localhost:9090/alerts, Grafana *Firing alerts* panels |

Grafana dashboards (folder *Credora*, provisioned from `observability/grafana/dashboards/*.json`):

| Dashboard | Shows |
| --- | --- |
| Services overview (home) | Up/down, request rate, 5xx ratio, p50/p95/p99 latency, in-flight requests, CPU and memory |
| API endpoints | Busiest, slowest and failing routes; per-route rate, latency and status codes |
| API gateway | Connections, requests/s, status codes, upstream latency, access log |
| Logs | Logs by service and level with text search, log volume and errors, request tracing by `X-Request-ID` |
| Platform health | Scrape targets, alerts, Loki ingestion, Jenkins build status |

Configuration lives in `observability/` and is built into the images, so changes take effect with `docker compose up -d --build`.

Example LogQL queries:

```logql
{service="customer-service"} | json | status >= 500
{service=~"gateway|customer-service|admin-service"} |= "<request id>"
```

### Logging

Both services write one JSON object per line to stdout:

```json
{"ts":"2026-10-31T13:32:08.650Z","level":"INFO","service":"customer-service","logger":"credora.access","message":"request completed","request_id":"verify-trace-001","method":"GET","path":"/api/v1/accounts","route":"/api/v1/accounts","status":401,"duration_ms":2.1,"client_ip":"172.20.0.1"}
```

- The gateway assigns an `X-Request-ID` (or keeps the caller's), passes it to the service and returns it in the response; every log line of that request carries it.
- The gateway access log is JSON as well (`gateway/nginx.conf`).
- `LOG_LEVEL` controls verbosity; health-check and `/metrics` requests are logged at `DEBUG`.
- Never logged: request or response bodies, `Authorization` headers, tokens, passwords, query strings, full account numbers.
- Business audit trails remain in the `audit_logs` and `security_events` tables.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| SonarQube or Jenkins slow to start / containers restarting | Give Docker Desktop at least 8 GB memory (*Settings → Resources*). SonarQube takes 1–2 minutes on first start. |
| `sonar-init` fails with an authentication error | `SONAR_ADMIN_PASSWORD` was changed after the first start. Use the original value, or reset with `docker compose -f ci/docker-compose.yml down -v` (deletes SonarQube and Jenkins data). |
| Pipeline waits at *Quality gate* | SonarQube must reach Jenkins through the webhook `http://jenkins:8080/sonarqube-webhook/` (created by `sonar-init`); check *Administration → Webhooks* in SonarQube. |
| A pipeline run replaced my local stack | Expected: Jenkins deploys to the same Docker engine. Run `docker compose up -d --build` to go back to the local source. |
| Jenkins does not see my changes | Jenkins builds what is pushed to `feature/cicd` on GitHub. Commit and push. |
| Shell scripts fail with `\r` errors | Line endings are forced to LF by `.gitattributes`; re-checkout the files (`git rm --cached -r . && git reset --hard`). |
| Jenkins target down in Prometheus | Normal while the CI stack is not running. |

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
