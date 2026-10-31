# Credora Microservices Architecture and Migration

| | |
|---|---|
| **Document** | Microservices architecture and migration record |
| **System** | Credora — Personal Banking Intelligence Platform (PBIP) |
| **Status** | Implemented |
| **Last updated** | 31 October 2026 |

---

## 1. Executive summary

Credora was migrated from a single FastAPI backend to a microservices architecture of three application services (frontend, customer service and admin service) behind an nginx API gateway, deployed with Docker Compose.

The migration followed one rule: **preserve all existing behaviour**. Every endpoint keeps its path, HTTP method, request and response contract, authentication rules and database behaviour. The services share the existing codebase and the Supabase PostgreSQL database, so business logic, data integrity and transactional guarantees are unchanged. An automated test verifies that the services together expose the complete API and that the gateway routes each endpoint to the correct service.

---

## 2. Target architecture

```
                        ┌───────────────────────────────┐
   Browser ──── :8080 ─►│     API gateway (nginx)       │
                        └──┬──────────────┬─────────────┘
                           │              │              │
          /api/v1/analytics│fraud│        │ /api/v1/*    │ /
                compliance │              │ (all other)  │
                           ▼              ▼              ▼
                 ┌──────────────┐ ┌─────────────────┐ ┌───────────┐
                 │ admin-service│ │customer-service │ │ frontend  │
                 │  (FastAPI)   │ │   (FastAPI)     │ │ (Next.js) │
                 └──────┬───────┘ └────────┬────────┘ └───────────┘
                        │                  │
                        └────────┬─────────┘
                                 ▼
                    Supabase PostgreSQL (public schema)
```

### 2.1 Service catalogue

| Service | Technology | Responsibility | Entry point |
|---|---|---|---|
| **gateway** | nginx 1.27 | Single public entry point. Path-based routing, request IDs, client IP forwarding, timeouts. | `gateway/nginx.conf` |
| **frontend** | Next.js 16 | Customer portal (`/login`, `/portal/*`) and internal banking workspace (`/admin/*`). | `frontend/Dockerfile` |
| **customer-service** | FastAPI | Authentication, customer profile, accounts, transactions, payees, transfers, bills, loans, investments, insurance, recommendations, AI assistant. | `backend/app/customer_main.py` |
| **admin-service** | FastAPI | Behavioural analytics, dashboard overview, customer directory, fraud investigations and alerts, compliance alerts, audit logs, security events. | `backend/app/admin_main.py` |

### 2.2 Design decisions

| Decision | Rationale | Trade-off |
|---|---|---|
| Split by deployment over a shared codebase | Each service mounts only its own routers from `backend/app`, so no business logic was rewritten and behaviour is identical. | Services are released from one codebase; a shared model change affects both. |
| Shared database, single `public` schema | Keeps foreign keys, joins and multi-table transactions intact (e.g. a transfer updates accounts, ledger, audit log, notifications and security events atomically). No data migration was needed. | Services are coupled at the schema level. |
| Shared login endpoint and JWT secret | Both portals keep using `POST /api/v1/auth/login`; a token is accepted by either service. No frontend authentication changes were needed. | Portal separation remains role-based rather than token-audience based. |
| nginx as gateway | Lightweight, standard, declarative path routing. | JWT validation stays in the services. |

### 2.3 Repository layout

```
PBIP/
├── docker-compose.yml          # full stack, migration and seed jobs
├── .env                        # runtime configuration (not committed)
├── gateway/
│   └── nginx.conf              # routing rules
├── frontend/
│   ├── Dockerfile
│   └── src/ …
└── backend/
    ├── Dockerfile              # one image, used by both services and the jobs
    ├── alembic/ …              # migrations
    ├── scripts/seed.py         # demo seed
    ├── data/generators/ …      # synthetic data generator
    ├── tests/
    │   └── test_service_split.py
    └── app/
        ├── customer_main.py    # customer-service entry point
        ├── admin_main.py       # admin-service entry point
        ├── main.py             # combined application (reference for tests)
        ├── core/app_factory.py # shared FastAPI setup (CORS, error handlers)
        ├── api/ services/ schemas/ models/ intelligence/
        └── core/ …
```

---

## 3. API gateway

### 3.1 Routing rules

| Order | Path match | Upstream |
|---|---|---|
| 1 | `= /healthz` | Gateway liveness (returns `ok`) |
| 2 | `~ ^/api/v1/(analytics\|fraud\|compliance)(/\|$)` | admin-service `:8000` |
| 3 | `/api/` | customer-service `:8000` |
| 4 | `/` | frontend `:3000` |

### 3.2 Gateway behaviour

- **Client IP forwarding:** sets `X-Real-IP` and `X-Forwarded-For` to the connecting client (overwritten, not appended, to prevent spoofing). The services run uvicorn with `--proxy-headers`, so audit logs and security events record the real client IP.
- **Request correlation:** forwards an incoming `X-Request-ID` or generates one, passes it upstream, returns it in the response and writes it to the access log.
- **Service discovery:** resolves upstreams per request through Docker DNS, so services can restart independently of the gateway.
- **Timeouts:** 5 s connect, 120 s read (covers AI assistant calls to the LLM provider).
- **Streaming:** proxy buffering is disabled for the frontend so Next.js can stream responses.

---

## 4. API-to-service mapping

All paths are relative to `/api/v1`. Authentication column: **Customer** = authenticated user with role `CUSTOMER` and a customer profile; **Authenticated** = any authenticated user; role lists = `require_roles(...)`; **Public** = no token.

### 4.1 customer-service

| Method | Endpoint | Module | Authentication | Primary tables |
|---|---|---|---|---|
| GET | `/health` | `api/health.py` | Public | — |
| POST | `/auth/register` | `api/auth.py` | Public | users, customers, audit_logs |
| POST | `/auth/login` | `api/auth.py` | Public | users, security_events, audit_logs |
| GET | `/me` | `api/me.py` | Authenticated | users |
| GET | `/customers/me` | `api/customers.py` | Customer | customers |
| PATCH | `/customers/me` | `api/customers.py` | Customer | customers, audit_logs |
| GET | `/customers/me/summary` | `api/customers.py` | Customer | accounts, transactions, payees, customer_investments, loan_applications |
| GET | `/accounts` | `api/accounts.py` | Customer | accounts |
| GET | `/accounts/{account_id}` | `api/accounts.py` | Customer | accounts |
| GET | `/accounts/{account_id}/transactions` | `api/accounts.py` | Customer | accounts, transactions |
| GET | `/transactions/{transaction_id}` | `api/transactions.py` | Customer | transactions, accounts |
| POST | `/payees` | `api/payees.py` | Customer | payees, audit_logs |
| GET | `/payees` | `api/payees.py` | Customer | payees |
| PATCH | `/payees/{payee_id}` | `api/payees.py` | Customer | payees, audit_logs |
| DELETE | `/payees/{payee_id}` | `api/payees.py` | Customer | payees, audit_logs |
| POST | `/transfers` | `api/transfers.py` | Customer | accounts, payees, transfers, transactions, audit_logs, notifications, security_events |
| GET | `/transfers` | `api/transfers.py` | Customer | transfers |
| GET | `/transfers/{transfer_id}` | `api/transfers.py` | Customer | transfers |
| POST | `/transfers/{transfer_id}/cancel` | `api/transfers.py` | Customer | transfers, audit_logs |
| GET | `/billers` | `api/bills.py` | Authenticated | billers |
| POST | `/bills/pay` | `api/bills.py` | Customer | accounts, billers, bill_payments, transactions, audit_logs, notifications |
| GET | `/bills/history` | `api/bills.py` | Customer | bill_payments |
| GET | `/loans/products` | `api/loans.py` | Authenticated | loan_products |
| GET | `/loans/products/{product_id}` | `api/loans.py` | Authenticated | loan_products |
| POST | `/loans/eligibility` | `api/loans.py` | Customer | loan_products, customers, customer_risk_profiles |
| POST | `/loans/applications` | `api/loans.py` | Customer | loan_products, loan_applications, customer_risk_profiles, audit_logs, notifications |
| GET | `/loans/applications` | `api/loans.py` | Customer | loan_applications |
| GET | `/loans/applications/{application_id}` | `api/loans.py` | Customer | loan_applications |
| GET | `/investments/products` | `api/investments.py` | Authenticated | investment_products |
| GET | `/investments/products/{product_id}` | `api/investments.py` | Authenticated | investment_products |
| GET | `/investments` | `api/investments.py` | Customer | customer_investments |
| POST | `/investments` | `api/investments.py` | Customer | investment_products, customer_investments, accounts, transactions, audit_logs |
| GET | `/insurance/products` | `api/insurance.py` | Authenticated | insurance_products |
| GET | `/insurance/products/{product_id}` | `api/insurance.py` | Authenticated | insurance_products |
| GET | `/recommendations` | `api/recommendations.py` | Customer | recommendations |
| POST | `/ai/chat` | `api/ai.py` | Customer | ai_conversations, ai_messages, accounts, transactions, customer_investments, loan_products, recommendations |
| GET | `/ai/conversations` | `api/ai.py` | Customer | ai_conversations |
| GET | `/ai/conversations/{conversation_id}` | `api/ai.py` | Customer | ai_conversations, ai_messages |

### 4.2 admin-service

| Method | Endpoint | Module | Authentication | Primary tables |
|---|---|---|---|---|
| GET | `/analytics/overview` | `intelligence/analytics/router.py` | ADMIN, RELATIONSHIP_MANAGER, FRAUD_ANALYST, COMPLIANCE_OFFICER | customers, users, accounts, transactions, behaviour_events, customer_risk_profiles, fraud_alerts, fraud_events |
| GET | `/analytics/customers` | `intelligence/analytics/router.py` | ADMIN, RELATIONSHIP_MANAGER, FRAUD_ANALYST, COMPLIANCE_OFFICER | customers, users, customer_risk_profiles, fraud_alerts, accounts |
| GET | `/analytics/behaviour` | `intelligence/analytics/router.py` | ADMIN, RELATIONSHIP_MANAGER | behaviour_events, customers, customer_risk_profiles |
| GET | `/analytics/behaviour/filters` | `intelligence/analytics/router.py` | ADMIN, RELATIONSHIP_MANAGER | behaviour_events, customers |
| GET | `/analytics/transactions` | `api/analytics.py` | RELATIONSHIP_MANAGER, ADMIN | — |
| GET | `/fraud/investigations` | `api/fraud.py` | FRAUD_ANALYST, ADMIN | fraud_investigations, fraud_alerts, fraud_events, customers, users |
| GET | `/fraud/alerts` | `api/fraud.py` | FRAUD_ANALYST, ADMIN | — |
| GET | `/fraud/alerts/{alert_id}` | `api/fraud.py` | FRAUD_ANALYST, ADMIN | — |
| PATCH | `/fraud/alerts/{alert_id}` | `api/fraud.py` | FRAUD_ANALYST, ADMIN | fraud_alerts, fraud_investigations, audit_logs |
| GET | `/fraud/customers/{customer_id}/risk` | `api/fraud.py` | FRAUD_ANALYST, ADMIN | — |
| GET | `/compliance/alerts` | `api/compliance.py` | COMPLIANCE_OFFICER, ADMIN | transactions, accounts, customers |
| GET | `/compliance/audit-logs` | `api/compliance.py` | COMPLIANCE_OFFICER, ADMIN | audit_logs, users, customers |
| GET | `/compliance/security-events` | `api/compliance.py` | COMPLIANCE_OFFICER, ADMIN, FRAUD_ANALYST | security_events, users, customers |

`/health`, `/auth/login`, `/auth/register` and `/me` are also mounted on admin-service so it can be operated on its own (for example from its Swagger UI on port 8002). Through the gateway these paths are served by customer-service.

### 4.3 Ownership criteria

Endpoints were assigned by inspecting their implementation, not their names:

- **customer-service:** endpoints that act on the authenticated customer's own resources and identity (JWT → user → customer → ownership check), and the product catalogues those journeys use.
- **admin-service:** endpoints that work across all customers for internal staff roles: aggregates, investigations, compliance and audit reporting.

For example, `/analytics/customers` is the internal customer directory and belongs to admin-service, while `/customers/me` is the customer's own profile and belongs to customer-service.

---

## 5. Authentication and authorization

| Aspect | Implementation |
|---|---|
| Credential check | `POST /api/v1/auth/login` validates email and bcrypt password hash, records `LOGIN_SUCCESS` / `LOGIN_FAILED` security events and a `USER_LOGIN` audit entry. |
| Token | HS256 JWT containing `sub` (user ID), `role` and `exp`; lifetime from `ACCESS_TOKEN_EXPIRE_MINUTES`. |
| Token validation | Each service validates the bearer token and loads the user from the database on every request, rejecting inactive accounts. |
| Authorization | `require_roles(...)` enforces role-based access per endpoint. Customer endpoints resolve the customer from the token and never accept a client-supplied `customer_id`. |
| Cross-service | Both services share `JWT_SECRET_KEY`, so one sign-in works across the customer and admin APIs. |
| Responses | `401` for missing/invalid tokens, `403` for insufficient role, `404` for resources owned by another customer. |

---

## 6. Data management

| Aspect | Implementation |
|---|---|
| Database | Supabase PostgreSQL, accessed through the transaction pooler (`DATABASE_URL`). |
| Schema | Single `public` schema shared by both services. |
| Transactions | Each operation runs in one local database transaction inside the service that handles it; no distributed transactions are required. |
| Migrations | Alembic, run by the `migrate` job with `alembic upgrade heads` (the history has two branches from revision `e5f6a7b8c9d0`). |
| Seed data | `seed` job: migrations → `scripts/seed.py` (demo users for every role, products, billers, recommendations) → `data/generators/generate.py` (synthetic customers, accounts, transactions, behaviour events, fraud scenarios, risk profiles). Both steps are idempotent. |
| Tests | Run against in-memory SQLite (or a dedicated `TEST_DATABASE_URL`); the test suite refuses to run against Supabase. |

---

## 7. Deployment

### 7.1 Docker Compose services

| Service | Image / build | Command | Ports |
|---|---|---|---|
| `gateway` | `nginx:1.27-alpine` | — | `8080:80` |
| `frontend` | `./frontend` (build arg `NEXT_PUBLIC_API_URL=http://localhost:8080/api/v1`) | `next start` | internal `3000` |
| `customer-service` | `./backend` | `uvicorn app.customer_main:app --proxy-headers` | `8001:8000` |
| `admin-service` | `./backend` | `uvicorn app.admin_main:app --proxy-headers` | `8002:8000` |
| `migrate` (profile `setup`) | `./backend` | `alembic upgrade heads` | — |
| `seed` (profile `seed`) | `./backend` | migrations + seed + generator | — |

Backend containers read configuration from the repository-root `.env` and report health through `GET /api/v1/health`, which Docker uses for health checks. A local PostgreSQL service is defined but commented out for teams that need an offline database.

### 7.2 Operations

```powershell
docker compose up --build -d                      # start the platform at http://localhost:8080
docker compose --profile setup run --rm migrate   # apply migrations
docker compose --profile seed run --rm seed       # migrations + demo and synthetic data
docker compose ps                                 # service status and health
docker compose logs -f gateway                    # routed requests with request IDs
docker compose down                               # stop the platform
```

### 7.3 Configuration

| Variable | Used by | Purpose |
|---|---|---|
| `DATABASE_URL` | customer-service, admin-service, jobs | Supabase PostgreSQL connection (asyncpg). |
| `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` | both services | Token signing and lifetime. |
| `GROQ_API_KEY`, `GROQ_MODEL` | customer-service | AI assistant. |
| `NEXT_PUBLIC_API_URL` | frontend (build time) | API base URL; points at the gateway. |

---

## 8. Migration approach

1. **Inventory.** Catalogued every endpoint with its method, implementation module, authentication, database tables and dependencies, and assigned each to a service based on its behaviour.
2. **Service entry points.** Added `customer_main.py` and `admin_main.py`, which build FastAPI applications from the existing routers using a shared factory (`core/app_factory.py`) that applies the same CORS policy and error handlers. No existing router, service, schema or model was modified.
3. **Gateway.** Added nginx with path-based routing, client IP forwarding and request correlation.
4. **Containerisation.** Added a frontend Dockerfile and `.dockerignore` files, and rewrote `docker-compose.yml` with the gateway, the three services, and migration and seed jobs.
5. **Verification.** Automated and end-to-end checks (section 9).
6. **Documentation.** Updated the README and team context documents.

---

## 9. Verification

| Check | Result |
|---|---|
| Backend test suite (including `test_service_split.py`) | 200 passed |
| Route coverage: customer routes ∪ admin routes = complete API | Passed |
| Gateway routing: every endpoint routed to a service that serves it | Passed |
| Service isolation: each service returns `404` for the other's routes | Passed |
| Customer journey through the gateway (login, profile, accounts, transactions, payees, transfers, bills, loans, investments, insurance, recommendations, AI) | Passed |
| Internal journey through the gateway (login, dashboard overview, customer directory, behaviour analytics, fraud investigations, alert update, compliance alerts, audit logs, security events) | Passed |
| Authorization through the gateway (`401` without token, `403` for wrong role) | Passed |
| Audit logs record the real client IP behind the gateway | Passed |
| Seed job (migrations, demo seed, synthetic data generation) | Passed |
| Frontend customer and admin portals load live data via the gateway | Passed |

---

## 10. Operational considerations

| Topic | Guidance |
|---|---|
| Database connections | Each service maintains its own connection pool (10 + 10 overflow). Monitor the Supabase connection count when scaling service replicas. |
| Frontend configuration | `NEXT_PUBLIC_API_URL` is compiled into the frontend bundle; rebuild the `frontend` image after changing it. |
| Adding endpoints | Register the router in `customer_main.py` or `admin_main.py`. New admin path prefixes must be added to the admin location in `gateway/nginx.conf`; `test_service_split.py` fails if a route is unmapped or misrouted. |
| Direct service ports | Ports 8001 and 8002 are for development and Swagger access; production traffic should enter only through the gateway. |

---

## 11. Future enhancements

- Centralised logging, metrics and distributed tracing (OpenTelemetry with a Grafana-based backend).
- Token audiences per service and service-to-service authentication.
- Independent data ownership per service (separate schemas or databases) if the services need to evolve independently.
