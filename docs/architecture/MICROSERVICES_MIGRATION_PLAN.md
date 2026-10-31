# Credora / PBIP — Monolith → Microservices Migration Plan

Status: **IMPLEMENTED** (2026-10-31) — see the "Architecture" section of the root README for how to run it.
Date: 2026-10-31 (revision 2, after review)

Implementation notes vs. this plan:
- `backend/app/core/app_factory.py` (new) holds the shared FastAPI setup used by `customer_main.py` and `admin_main.py`; `app/main.py` is untouched.
- The compose file also keeps the old monolith as profile `monolith` (port 8000) for fallback.
- New `.dockerignore` files keep `.venv`, `node_modules`, `.next` and `.env` out of the images.

## 0. Decisions (from review)

| Topic | Decision |
|---|---|
| Database | **Keep the single existing `public` schema.** No schema split, no table moves, no new migrations. |
| Login | **Keep the shared `POST /api/v1/auth/login` exactly as it is.** Both portals keep using it; the frontend keeps its existing role checks. |
| API code | **No changes to existing endpoints, services, schemas, models or business logic.** If it works in the monolith, it stays as it is. |
| Pre-existing quirks | Left as is (admin login page role filter, the 4 stub endpoints, scheduled transfers with no executor). |
| Monitoring / tracing | **Deferred** to a later phase. |
| Seeder | **Must work** in the new setup (migrations + `scripts/seed.py` + `data/generators/generate.py`). |

> `CUSTOMER_TEAM_CONTEXT.md` / `INTERNAL_TEAM_CONTEXT.md` say "Do NOT introduce microservices"; those lines should be updated when this is implemented.

---

## 1. Approach: split by deployment, not by rewriting

The existing `backend/app` package stays the single source of code. The split happens at **runtime**:

- **customer-service** = a container running the existing code, mounting only the customer routers.
- **admin-service** = a container running the same code, mounting only the internal routers.
- **gateway (nginx)** decides which container gets each request.
- **frontend** gets its own container.

Both services connect to the same database with the same `.env` (same JWT secret), so a token issued by `/auth/login` is valid on both. Every endpoint keeps its path, method, request, response, auth rule and DB behaviour.

**Why this way:** nothing in the business logic, models or migrations has to change, so there is nothing to break. Each service can still be scaled and restarted on its own, and API ownership is clearly split at the gateway.
**Trade-off:** the two services share one codebase and one database (a "shared-database" split). They are not independently versioned, and a model change affects both. That is acceptable for this project. A full code/DB separation can come later if needed.

### What will be added when implemented (new files only — no existing file edited)

| New file | Purpose |
|---|---|
| `backend/app/customer_main.py` | FastAPI app that includes only the customer routers (same settings, CORS, exception handlers as `app/main.py`). |
| `backend/app/admin_main.py` | FastAPI app that includes only the internal routers. |
| `backend/tests/test_service_split.py` | Guard test: customer routes ∪ admin routes == monolith routes, and the gateway sends every route to a service that serves it. |
| `gateway/nginx.conf` | Routing rules (section 3). |
| `frontend/Dockerfile` | Builds/serves Next.js. |
| `docker-compose.yml` | Rewritten (section 5). The only existing file replaced. |

`backend/app/main.py` (the monolith) stays and keeps working, so you can fall back to it at any time.

---

## 2. API inventory and service mapping

All paths are under `/api/v1`. **No endpoint is modified.** Auth: **C** = customer only (`get_current_customer`), **U** = any logged-in user, **R(…)** = specific roles, **—** = public.

### 2.1 customer-service

| # | Method | Endpoint | Code location | Auth | Main tables |
|---|---|---|---|---|---|
| 1 | GET | `/health` | `api/health.py` | — | — |
| 2 | POST | `/auth/register` | `api/auth.py` | — | users, customers, audit_logs |
| 3 | POST | `/auth/login` (**shared by both portals**) | `api/auth.py` | — | users, security_events, audit_logs |
| 4 | GET | `/me` | `api/me.py` | U | users |
| 5–7 | GET / PATCH / GET | `/customers/me`, `/customers/me`, `/customers/me/summary` | `api/customers.py` | C | customers, accounts, transactions, payees, customer_investments, loan_applications, audit_logs |
| 8–10 | GET | `/accounts`, `/accounts/{id}`, `/accounts/{id}/transactions` | `api/accounts.py` | C | accounts, transactions |
| 11 | GET | `/transactions/{id}` | `api/transactions.py` | C | transactions, accounts |
| 12–15 | POST / GET / PATCH / DELETE | `/payees`, `/payees/{id}` | `api/payees.py` | C | payees, audit_logs |
| 16–19 | POST / GET / GET / POST | `/transfers`, `/transfers/{id}`, `/transfers/{id}/cancel` | `api/transfers.py` | C | accounts, payees, transfers, transactions, audit_logs, notifications, security_events |
| 20 | GET | `/billers` | `api/bills.py` | U | billers |
| 21–22 | POST / GET | `/bills/pay`, `/bills/history` | `api/bills.py` | C | accounts, billers, bill_payments, transactions, audit_logs, notifications |
| 23–24 | GET | `/loans/products`, `/loans/products/{id}` | `api/loans.py` | U | loan_products |
| 25–28 | POST / POST / GET / GET | `/loans/eligibility`, `/loans/applications`, `/loans/applications/{id}` | `api/loans.py` | C | loan_products, loan_applications, customer_risk_profiles, audit_logs, notifications |
| 29–30 | GET | `/investments/products`, `/investments/products/{id}` | `api/investments.py` | U | investment_products |
| 31–32 | GET / POST | `/investments` | `api/investments.py` | C | customer_investments, investment_products, accounts, transactions, audit_logs |
| 33–34 | GET | `/insurance/products`, `/insurance/products/{id}` | `api/insurance.py` | U | insurance_products |
| 35 | GET | `/recommendations` | `api/recommendations.py` | C | recommendations |
| 36–38 | POST / GET / GET | `/ai/chat`, `/ai/conversations`, `/ai/conversations/{id}` | `api/ai.py` | C | ai_conversations, ai_messages + customer tables; calls Groq |

### 2.2 admin-service

| # | Method | Endpoint | Code location | Auth | Main tables |
|---|---|---|---|---|---|
| 39 | GET | `/analytics/overview` | `intelligence/analytics/router.py` | R(ADMIN, RM, FRAUD_ANALYST, COMPLIANCE_OFFICER) | customers, users, accounts, transactions, behaviour_events, customer_risk_profiles, fraud_* |
| 40 | GET | `/analytics/customers` | same | R(same 4) | customers, users, customer_risk_profiles, fraud_alerts, accounts |
| 41–42 | GET | `/analytics/behaviour`, `/analytics/behaviour/filters` | same | R(ADMIN, RM) | behaviour_events, customers |
| 43 | GET | `/analytics/transactions` (stub) | `api/analytics.py` | R(RM, ADMIN) | — |
| 44 | GET | `/fraud/investigations` | `api/fraud.py` | R(FRAUD_ANALYST, ADMIN) | fraud_investigations, fraud_alerts, fraud_events, customers, users |
| 45–46 | GET | `/fraud/alerts`, `/fraud/alerts/{id}` (stubs) | `api/fraud.py` | R(FRAUD_ANALYST, ADMIN) | — |
| 47 | PATCH | `/fraud/alerts/{id}` | `api/fraud.py` | R(FRAUD_ANALYST, ADMIN) | fraud_alerts, fraud_investigations, audit_logs |
| 48 | GET | `/fraud/customers/{id}/risk` (stub) | `api/fraud.py` | R(FRAUD_ANALYST, ADMIN) | — |
| 49 | GET | `/compliance/alerts` | `api/compliance.py` | R(COMPLIANCE_OFFICER, ADMIN) | transactions, accounts, customers |
| 50 | GET | `/compliance/audit-logs` | `api/compliance.py` | R(COMPLIANCE_OFFICER, ADMIN) | audit_logs, users, customers |
| 51 | GET | `/compliance/security-events` | `api/compliance.py` | R(COMPLIANCE_OFFICER, ADMIN, FRAUD_ANALYST) | security_events, users, customers |

Also mounted on admin-service (identical code, so it can be used alone, e.g. from its own Swagger UI): `/health`, `/auth/login`, `/auth/register`, `/me`. Through the gateway these paths still go to customer-service.

Ownership was decided from what each endpoint actually does, not just its name. For example, `/analytics/customers` is the internal customer directory, so it goes to admin. `/customers/me` is a customer's own profile, so it goes to customer.

### 2.3 Cross-service dependencies
None at the HTTP level. Both services read and write the shared database exactly as the monolith does today, so no service calls the other.

---

## 3. API gateway (nginx) routing

| Path | Goes to |
|---|---|
| `^/api/v1/(analytics\|fraud\|compliance)(/\|$)` | admin-service |
| `/api/v1/` (everything else, including `/auth/login`) | customer-service |
| `/` | frontend |
| `/healthz` | gateway itself |

Gateway also: forwards `X-Forwarded-For` / `X-Real-IP` / `X-Forwarded-Proto`, and generates `X-Request-ID`.

Swagger UI: each service exposes its own `/docs` on a host port (customer `8001`, admin `8002`) for development.

---

## 4. Frontend
- No source code changes.
- `NEXT_PUBLIC_API_URL` is set at **build time** (a Docker build arg) to the gateway: `http://localhost:8080/api/v1`. The frontend is also served by the gateway on `:8080`, so the existing CORS list doesn't need changing when the app is opened at `http://localhost:8080`.

---

## 5. Docker Compose (target)

| Service | Built from | Command / notes | Port |
|---|---|---|---|
| `gateway` | `nginx` (pinned version) + `gateway/nginx.conf` | depends on the 3 app services | **8080** (public entry) |
| `frontend` | `./frontend` | `next start -H 0.0.0.0 -p 3000` | internal |
| `customer-service` | `./backend` (existing Dockerfile) | `uvicorn app.customer_main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips=*` | 8001 → 8000 |
| `admin-service` | `./backend` (same image) | `uvicorn app.admin_main:app … --proxy-headers --forwarded-allow-ips=*` | 8002 → 8000 |
| `migrate` (one-shot, profile `setup`) | `./backend` | `alembic upgrade head` | — |
| `seed` (one-shot, profile `seed`) | `./backend` | `alembic upgrade head && python -m scripts.seed && python -m data.generators.generate` | — |
| `postgres` (optional, profile `local-db`) | `postgres:16` | Local DB for trying things out without touching Supabase | 5432 |

All backend containers use `env_file: ./backend/.env` exactly like today. Both services use the same image, so the seeder and migrations run the existing code unchanged.

### Seeder — how it will work
```bash
docker compose --profile seed run --rm seed
```
1. `alembic upgrade head` — creates/updates tables (existing 8 revisions, untouched).
2. `python -m scripts.seed` — demo users for all 5 roles (password `PBIP@Demo123`), accounts, transactions, products, billers, recommendations. Safe to re-run (get-or-create).
3. `python -m data.generators.generate` — synthetic customers, transactions, behaviour events, fraud scenarios, risk profiles. Skips if data exists; `--reset` regenerates.

⚠️ This writes to whatever `DATABASE_URL` points at. If that's the shared Supabase DB, teammates see the data. Use the `local-db` profile to try it first.

---

## 6. Issues to watch for (with the plan for each)

| # | Issue | Plan |
|---|---|---|
| 1 | **Client IP lost behind nginx** — audit logs / security events would record the gateway's IP | nginx sends `X-Forwarded-For`; uvicorn runs with `--proxy-headers` (a startup flag, no code change). |
| 2 | **`NEXT_PUBLIC_API_URL` is baked in at build** | Passed as a Docker build arg; rebuild the frontend if the URL changes. |
| 3 | **Route collisions** (`/customers/me` vs `/analytics/customers`, `/fraud/customers/{id}/risk`) | Gateway matches on the first path segment after `/api/v1`; the guard test checks every route. |
| 4 | **DB connection limits** — two services, each with a pool of 10 + 10 overflow, against Supabase | Watch Supabase connection count; use the pooler URL; lower pool size later if needed. |
| 5 | **Gateway as single point of failure** | Fine for dev/academic use; healthchecks + `restart: unless-stopped`. |
| 6 | **Startup ordering** | `depends_on` + healthchecks on `/api/v1/health`. |
| 7 | **Shared codebase coupling** | Accepted trade-off (section 1); the monolith entrypoint stays as a fallback. |
| 8 | **Seeder hitting shared data** | Separate `seed` profile; `local-db` option. |
| 9 | **Missing `backend/.env`** in a fresh checkout | Copy `backend/.env.example`; documented in README. |

## 7. Deferred (later phases)
- Centralised logging / tracing (OpenTelemetry + Grafana stack).
- Separate login per portal / per-service JWT audiences.
- Separate schemas or databases per service.
- Fixing the pre-existing quirks listed in section 0.

## 8. Implementation order (when approved)
1. Add `customer_main.py`, `admin_main.py` and the guard test; run the existing test suite plus the guard test.
2. Add `gateway/nginx.conf` and `frontend/Dockerfile`.
3. Rewrite `docker-compose.yml` with the services and profiles above.
4. Run on `local-db`: migrate → seed → log in as a customer and as an admin through `:8080`, then check the main pages for both portals.
5. Update README and the team-context docs.
