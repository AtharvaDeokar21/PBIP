# Credora CI/CD and Observability Plan

| | |
|---|---|
| **Document** | CI/CD pipeline, static analysis and observability plan |
| **System** | Credora — Personal Banking Intelligence Platform (PBIP) |
| **Source** | `https://github.com/AtharvaDeokar21/PBIP` (public), branch `feature/cicd` |
| **Status** | Implemented |
| **Date** | 31 October 2026 |

---

## 1. Objectives and decisions

| # | Objective | Delivered by |
|---|---|---|
| 1 | Prepare the build | Pipeline stages *Checkout* and *Prepare* |
| 2 | Run all backend tests | Stage *Backend tests* (pytest, JUnit + coverage reports) |
| 3 | Static analysis with SonarQube | Stages *SonarQube analysis* and *Quality gate* (blocking) |
| 4 | Build frontend and backend and run them | Stages *Build images* and *Deploy* |
| 5 | Seed the database | Stage *Seed database* |
| 6 | Observability | Prometheus, Loki + Grafana Alloy, Grafana with provisioned dashboards |
| 7 | Proper service logging | Structured JSON logs with request correlation |
| 8 | Zero manual setup | Every credential, token, job and integration provisioned automatically from the root `.env` |

| Decision | Outcome |
|---|---|
| Observability | **Always on** — starts with the application stack. |
| Pipeline source | **GitHub, public repository, branch `feature/cicd`**. No GitHub credential needed. |
| Quality gate failure | **Aborts the pipeline.** |
| SonarQube storage | **Embedded H2 database** (no extra database container). |
| CI tooling | **Separate Docker Compose project** (`ci/docker-compose.yml`). |
| Smoke tests | **Not included.** Deployment success is determined by container health checks. |

Constraint carried over from the migration: **no change to API behaviour or business logic.** Code changes are limited to the shared app factory (logging and metrics middleware), a new logging module and dependencies.

---

## 2. Topology

```
                         ┌──────────────── CI stack: ci/docker-compose.yml (project credora-ci) ───────────────┐
 GitHub                  │                                                                                      │
 feature/cicd ──poll───► │  Jenkins :8081 ──withSonarQubeEnv──► SonarQube :9000 ◄── sonar-init (one-shot):     │
                         │     │   ▲                                   │              admin password, project,  │
                         │     │   └────── webhook (quality gate) ─────┘              quality gate, token,      │
                         │     │                                                       webhook                  │
                         │     │ host Docker socket                    token ──► shared volume ──► Jenkins JCasC │
                         └─────┼────────────────────────────────────────────────────────────────────────────────┘
                               │ docker compose build / up --wait / run seed
                               ▼
 ┌────────────── Application stack: docker-compose.yml (project credora) ─────────────────────────────────────────┐
 │  gateway :8080 ──► frontend │ customer-service :8001 │ admin-service :8002 ──► Supabase PostgreSQL              │
 │                                                                                                                │
 │  Prometheus :9090 ◄── /metrics: services, nginx-exporter, Loki, Alloy, Grafana, Jenkins                       │
 │  Grafana Alloy :12345 ── container stdout via Docker API ──► Loki :3100                                        │
 │  Grafana :3001 ◄── Prometheus + Loki (provisioned datasources, dashboards, alert rules)                        │
 └────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

| Project | File | Contents |
|---|---|---|
| `credora` | `docker-compose.yml` (includes `observability/compose.yml`) | Application and observability — what Jenkins builds and runs. |
| `credora-ci` | `ci/docker-compose.yml` | Jenkins, SonarQube, `sonar-init`. Independent of application redeploys. |

---

## 3. Automation — no manual credential handling

Everything is configured from the **repository-root `.env`** (already present for Supabase). New keys are added with safe defaults in a committed `.env.example`.

| Key | Default | Used by |
|---|---|---|
| `DATABASE_URL`, `JWT_*`, `GROQ_*` | — (existing) | Application services, seed job |
| `JENKINS_ADMIN_USER` / `JENKINS_ADMIN_PASSWORD` | `admin` / `admin` | Jenkins (JCasC) |
| `SONAR_ADMIN_PASSWORD` | `Credora@Sonar1` | `sonar-init` replaces SonarQube's default `admin/admin` |
| `GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD` | `admin` / `admin` | Grafana |
| `LOG_LEVEL` | `INFO` | Application services |

| What | How it is automated |
|---|---|
| Jenkins setup wizard | Disabled (`-Djenkins.install.runSetupWizard=false`). |
| Jenkins admin user | Created by JCasC from `JENKINS_ADMIN_*`. |
| Jenkins plugins | Pre-installed in the custom image from `ci/jenkins/plugins.txt`. |
| Application secrets for the pipeline | The root `.env` is mounted read-only into Jenkins; JCasC creates the `credora-env` *secret file* credential from it (`${readFileBase64:…}`). The pipeline writes it to the workspace for each run. |
| SonarQube admin password | `sonar-init` changes it from the default on first start. |
| SonarQube project, quality gate, webhook | Created by `sonar-init` through the SonarQube Web API (idempotent). |
| SonarQube analysis token | Generated by `sonar-init`, written to a volume shared only with Jenkins; JCasC loads it as the `sonar-token` credential and binds it to the `sonarqube` server entry. |
| Pipeline job | Created by JCasC + Job DSL: *Pipeline from SCM*, `https://github.com/AtharvaDeokar21/PBIP.git`, branch `feature/cicd`, script `Jenkinsfile`. |
| First build | Started by SCM polling within 2 minutes of Jenkins starting (the job has no previous build); afterwards every push to `feature/cicd`. |
| Grafana datasources and dashboards | Provisioned from files baked into the Grafana image. |

**Start-up order** (enforced with `depends_on`): SonarQube healthy → `sonar-init` completed successfully → Jenkins starts and loads the token.

Result: `docker compose up -d` (application) and `docker compose -f ci/docker-compose.yml --env-file .env up -d --build` (CI) are the only commands needed. No UI clicks, no copied tokens.

---

## 4. Jenkins pipeline

### 4.1 Jenkins image and configuration

| Item | Approach |
|---|---|
| Image | `ci/jenkins/Dockerfile`: `jenkins/jenkins:lts-jdk21` + Docker CLI + Compose plugin + plugins. |
| Plugins | `workflow-aggregator`, `git`, `docker-workflow`, `sonar`, `junit`, `coverage`, `credentials-binding`, `configuration-as-code`, `job-dsl`, `timestamper`, `ws-cleanup`, `prometheus`. |
| Configuration as code | `ci/jenkins/casc.yaml`: security realm and admin user, credentials (`credora-env`, `sonar-token`), SonarQube server `sonarqube` → `http://sonarqube:9000`, Prometheus endpoint, pipeline job definition. |
| Docker access | Host Docker socket mounted (docker-outside-of-docker). Build containers are started by `docker-workflow`, which shares the Jenkins workspace volume automatically. |
| Port | `8081` (8080 is the application gateway). |

### 4.2 Stages (`Jenkinsfile`, declarative)

| # | Stage | Runs in | What it does | Fails when |
|---|---|---|---|---|
| 1 | **Checkout** | Jenkins | Clean workspace; checkout `feature/cicd`; record commit SHA. | Checkout fails. |
| 2 | **Prepare** | Jenkins | Print tool versions; write `.env` from `credora-env`; `docker compose config --quiet`; set image tag `${BUILD_NUMBER}-${SHORT_SHA}`. | Invalid configuration. |
| 3a | **Backend tests** *(parallel)* | `python:3.12-slim` | Install requirements + `pytest-cov`; `pytest` → `reports/junit.xml`, `reports/coverage.xml`; `ruff check` → `reports/ruff.json` (input for SonarQube, non-blocking on its own). | Any test fails. |
| 3b | **Frontend checks** *(parallel)* | `node:22-bookworm-slim` | `npm ci`; `npm run typecheck`. | Type errors. |
| 4 | **SonarQube analysis** | `sonarsource/sonar-scanner-cli` on the CI network | `withSonarQubeEnv('sonarqube')` → scanner with `sonar-project.properties`, imports test, coverage and Ruff reports. | Scanner error. |
| 5 | **Quality gate** | Jenkins | `waitForQualityGate abortPipeline: true` (result delivered by the SonarQube webhook; 10-minute timeout). | Gate status is not `OK`. |
| 6 | **Build images** | Host Docker | `docker compose -f docker-compose.yml -f docker-compose.ci.yml build` — backend, frontend, gateway and observability images. | Build error. |
| 7 | **Deploy** | Host Docker | `docker compose … up -d --remove-orphans --wait --wait-timeout 300` — returns only when every service with a health check is healthy. | A service is unhealthy or exits. |
| 8 | **Seed database** | Host Docker | `docker compose … --profile seed run --rm seed` (migrations → demo seed → synthetic generator; idempotent). Parameter `SEED_DB`, default `true`. | Seed job exits non-zero. |
| — | **Post** | Jenkins | Publish JUnit and coverage; archive `reports/`; link to the SonarQube project; on failure print `docker compose ps` and the last 200 log lines per service; clean workspace. The deployed stack keeps running. | — |

Pipeline options: `timestamps()`, `disableConcurrentBuilds()`, `buildDiscarder(logRotator(numToKeepStr: '20'))`, overall timeout 60 minutes.

### 4.3 Supporting files

| File | Purpose |
|---|---|
| `Jenkinsfile` | Pipeline definition. |
| `docker-compose.ci.yml` | Override for pipeline runs: removes source bind mounts and `--reload`, so containers run purely from built images (see §8, risk 1). |
| `.gitattributes` | Forces LF line endings for `Jenkinsfile`, `*.sh`, `*.conf`, `*.yml`, `*.yaml`, `*.alloy`, `*.properties`. |

---

## 5. SonarQube

### 5.1 Server

| Item | Setting |
|---|---|
| Image | `sonarqube:<pinned>-community` |
| Storage | Embedded H2 in named volumes (`sonarqube-data`, `sonarqube-extensions`, `sonarqube-logs`). |
| Docker Desktop compatibility | `SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true` (no host `vm.max_map_count` change needed). |
| Health check | `GET /api/system/status` → `UP`. |
| Port | `9000` |

> Embedded H2 is supported by SonarQube for evaluation use and cannot be upgraded in place to a later SonarQube version; data is kept in volumes across restarts. Moving to PostgreSQL later only requires adding a database service and the `SONAR_JDBC_*` variables.

### 5.2 Automated provisioning (`ci/sonar-init/`)

A one-shot container runs an idempotent script against the Web API:

| Step | API | Result |
|---|---|---|
| 1 | `GET /api/system/status` (retry) | Waits until SonarQube is `UP`. |
| 2 | `POST /api/users/change_password` | Default `admin/admin` → `SONAR_ADMIN_PASSWORD` (skipped if already changed). |
| 3 | `POST /api/projects/create` | Project `credora` / name *Credora*. |
| 4 | `POST /api/qualitygates/select` | Assigns the quality gate (§5.4) to the project. |
| 5 | `POST /api/settings/set` | New-code definition: previous version. |
| 6 | `POST /api/webhooks/create` | `http://jenkins:8080/sonarqube-webhook/` for quality-gate results. |
| 7 | `POST /api/user_tokens/revoke` + `generate` | Fresh project analysis token written to the shared `sonar-secrets` volume. |

### 5.3 Analysis configuration (`sonar-project.properties`)

| Property | Value |
|---|---|
| `sonar.projectKey` / `sonar.projectName` | `credora` / `Credora` |
| `sonar.sources` | `backend/app, backend/scripts, frontend/src` |
| `sonar.tests` | `backend/tests, frontend/tests` |
| `sonar.exclusions` | `**/node_modules/**, **/.next/**, backend/alembic/versions/**` |
| `sonar.python.version` | `3.12` |
| `sonar.python.coverage.reportPaths` | `backend/reports/coverage.xml` (generated with `relative_files = True` via `backend/.coveragerc`) |
| `sonar.python.xunit.reportPath` | `backend/reports/junit.xml` |
| `sonar.python.ruff.reportPaths` | `backend/reports/ruff.json` |
| `sonar.typescript.tsconfigPaths` | `frontend/tsconfig.json` |
| `sonar.coverage.exclusions` | `frontend/**, backend/tests/**, backend/data/**, backend/scripts/**, backend/alembic/**` (no frontend unit-test coverage exists) |
| `sonar.sourceEncoding` | `UTF-8` |
| `sonar.qualitygate.wait` | not used — the Jenkins `waitForQualityGate` step handles it. |

The Community edition analyses a single branch; the `feature/cicd` analysis is stored as the project's main branch.

### 5.4 Quality gate

**Sonar way** (SonarQube's default, "clean as you code"): on new code — no new issues, all new security hotspots reviewed, coverage ≥ 80 %, duplication ≤ 3 %.

Because the gate is evaluated on **new code**, the first analysis establishes the baseline and later builds fail only for problems introduced by new changes. This keeps the gate blocking (as decided) without failing on the existing codebase.

---

## 6. Logging

### 6.1 Format

One JSON object per line on stdout:

```json
{"ts":"2026-10-31T10:54:17.123Z","level":"INFO","service":"customer-service","logger":"credora.access",
 "message":"request completed","request_id":"52298d58485654ac553626fa4870cfa4",
 "method":"POST","route":"/api/v1/auth/login","status":401,"duration_ms":468.2,"client_ip":"172.20.0.1"}
```

| Field | Source |
|---|---|
| `service` | `SERVICE_NAME` per container. |
| `request_id` | `X-Request-ID` from the gateway (generated if absent), held in a context variable so every log line within the request carries it; returned in the response header. |
| `route` | Route template (e.g. `/api/v1/accounts/{account_id}`), not the raw path. |
| `client_ip` | Real client IP (gateway forwarding + uvicorn `--proxy-headers`). |

### 6.2 Implementation

| Component | Change |
|---|---|
| `backend/app/core/logging.py` (new) | JSON formatter, `LOG_LEVEL`, request-id context filter, configures root and uvicorn loggers. |
| `backend/app/core/app_factory.py` | Middleware: request id, timing, one access record per request, unhandled exceptions logged at `ERROR` with stack trace. Health and `/metrics` requests logged at `DEBUG`. |
| Service command | uvicorn `--no-access-log` (replaced by the structured access record). |
| Gateway | nginx `log_format … escape=json`: time, request id, method, URI, status, bytes, request time, upstream address and time. |
| Frontend | Next.js stdout collected as plain text. |

**Never logged:** request or response bodies, `Authorization` headers, tokens, passwords, query strings, full account numbers. Business audit (`audit_logs`, `security_events`) stays in the database.

---

## 7. Observability stack (always on)

All configuration lives in `observability/` and is **copied into small images** (no bind mounts), so it works identically when started locally and when deployed by Jenkins.

| Component | Image | Port | Role |
|---|---|---|---|
| Prometheus | `prom/prometheus:<pinned>` | 9090 | Scrapes every 15 s, 15-day retention, alert rules. |
| Loki | `grafana/loki:<pinned>` | 3100 | Log store (single binary, filesystem, 7-day retention). |
| Grafana Alloy | `grafana/alloy:<pinned>` | 12345 | Discovers containers through the Docker API, ships stdout to Loki, extracts JSON fields. Replaces Promtail (end-of-life March 2026). |
| nginx exporter | `nginx/nginx-prometheus-exporter:<pinned>` | internal 9113 | Gateway connection and request metrics from an internal `stub_status` endpoint. |
| Grafana | `grafana/grafana:<pinned>` | 3001 | Dashboards; datasources, dashboards and alert rules provisioned from files. |

### 7.1 Metrics

| Source | Endpoint | Metrics |
|---|---|---|
| customer-service, admin-service | `/metrics` (`prometheus-fastapi-instrumentator`; not routed by the gateway) | Request count by route/method/status, latency histogram, in-flight requests, process CPU/memory/GC; label `service`. |
| Gateway | nginx exporter | Active/accepted/handled connections, requests. |
| Prometheus, Loki, Alloy, Grafana | built-in `/metrics` | Stack self-monitoring. |
| Jenkins | `host.docker.internal:8081/prometheus/` | Build results, durations, queue length. |

Alert rules (`observability/prometheus/alerts.yml`): service down > 1 min; 5xx ratio > 5 % for 5 min; p95 latency > 1 s for 5 min; gateway down; last Jenkins build failed.

### 7.2 Logs

Loki labels (low cardinality only): `service`, `container`, `level`, `logger`, `stream`. Request-level fields stay in the JSON body:

```logql
{service="customer-service"} | json | status >= 500
{service=~"gateway|customer-service|admin-service"} | json | request_id="<id>"
```

### 7.3 Grafana provisioning

```
observability/grafana/
├── Dockerfile
├── provisioning/
│   ├── datasources/datasources.yaml   # Prometheus (default) and Loki, fixed UIDs
│   └── dashboards/dashboards.yaml     # file provider → folder "Credora"
└── dashboards/
    ├── credora-services-overview.json
    ├── credora-api-endpoints.json
    ├── credora-gateway.json
    ├── credora-logs.json
    └── credora-platform-health.json
```

| Dashboard | Key panels |
|---|---|
| Services overview | Up/down, request rate, 5xx %, p50/p95/p99 latency, in-flight requests, CPU and memory per service. |
| API endpoints | Top routes by traffic, slowest routes, error routes; variables `service`, `route`. |
| Gateway | Connections, requests/s, status codes and upstream latency (from JSON access logs). |
| Logs | Live logs by `service`/`level`, error rate, `request_id` search across gateway and services. |
| Platform health | Prometheus target health, Loki ingestion, firing alerts, Jenkins build success rate and duration. |

---

## 8. Risks and mitigations

| # | Risk | Mitigation |
|---|---|---|
| 1 | Bind mounts resolve inside the Jenkins container when Jenkins drives the host Docker. | `docker-compose.ci.yml` removes source mounts; all observability and gateway configs are baked into images. |
| 2 | Each pipeline run replaces the `credora` stack on the same Docker host. | Intended — Jenkins is the deployer. Documented in the README. |
| 3 | Seeding writes to the shared Supabase database. | Idempotent job; `SEED_DB` parameter. |
| 4 | Secrets exposure. | Root `.env` mounted read-only, stored as Jenkins credentials, never echoed (credentials masking); SonarQube token kept in a volume shared only with Jenkins; workspace cleaned after each run; `.gitignore` covers all secret and report paths (§9). |
| 5 | Docker socket access gives Jenkins root-equivalent access to the host. | Acceptable for a local CI environment; documented. |
| 6 | Resource usage (SonarQube ≈ 2 GB). | Docker Desktop memory ≥ 8 GB recommended for CI + application + observability. |
| 7 | Jenkins only builds what is pushed to `feature/cicd`. | Documented; local changes must be committed and pushed to trigger a build. |
| 8 | Windows line endings break Linux containers. | `.gitattributes`. |
| 9 | `backend/requirements.txt` is UTF-16. | Re-encoded as UTF-8 (content unchanged) before adding `prometheus-fastapi-instrumentator`. |
| 10 | Log volume and label cardinality. | Low-cardinality labels only; health/metrics at DEBUG; 7-day retention. |
| 11 | Embedded H2 cannot be upgraded with SonarQube. | Pinned SonarQube version; PostgreSQL migration path documented. |

---

## 9. `.gitignore`

The existing root and frontend `.gitignore` files are valid but do not cover CI and tooling outputs. Additions:

```gitignore
# Secrets / environment
.env
.env.*
!.env.example
backend/.env

# Test and analysis reports
backend/reports/
.coverage
coverage.xml
htmlcov/
.scannerwork/
.sonar/

# Tooling
.claude/
*.local.yml
```

Committed: `.env.example` (root, with all keys and defaults from §3). Never committed: `.env`, generated tokens (they live only in Docker volumes), reports.

---

## 10. URLs and ports (added to the README)

| Service | URL | Credentials |
|---|---|---|
| Credora app (gateway) | http://localhost:8080 | Demo users from the seed (`PBIP@Demo123`) |
| Customer portal | http://localhost:8080/login | Customer account |
| Internal banking portal | http://localhost:8080/admin/login | Staff account |
| Customer service API docs | http://localhost:8001/docs | — |
| Admin service API docs | http://localhost:8002/docs | — |
| Grafana | http://localhost:3001 | `GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD` |
| Prometheus | http://localhost:9090 (targets: `/targets`, alerts: `/alerts`) | — |
| Loki | http://localhost:3100/ready (API only; browse logs in Grafana) | — |
| Grafana Alloy | http://localhost:12345 | — |
| Jenkins | http://localhost:8081 | `JENKINS_ADMIN_USER` / `JENKINS_ADMIN_PASSWORD` |
| SonarQube | http://localhost:9000 (project: `/dashboard?id=credora`) | `admin` / `SONAR_ADMIN_PASSWORD` |

Internal only (not published): frontend `3000`, services `8000`, nginx exporter `9113`, nginx `stub_status`.

---

## 11. README updates

1. **Platform overview** — Jenkins, SonarQube, Prometheus, Loki, Alloy, Grafana.
2. **URLs and ports** — the table in §10.
3. **Configuration** — root `.env` and `.env.example` keys (§3).
4. **Running the platform** — application + observability with one command.
5. **CI/CD** — start the CI stack with one command; what is provisioned automatically; how builds are triggered (push to `feature/cicd`, or *Build Now*); stages; `SEED_DB`; where test, coverage and SonarQube results appear.
6. **Static analysis** — SonarQube project, quality gate behaviour, running a scan.
7. **Observability** — dashboards, alert rules, example LogQL, tracing a request with `X-Request-ID`.
8. **Logging** — format, fields, `LOG_LEVEL`, never-logged data.
9. **Troubleshooting** — Docker Desktop memory, SonarQube start-up time, quality gate pending, stack replaced by a pipeline run, line endings.

---

## 12. Changes summary

**New**

```
Jenkinsfile
docker-compose.ci.yml
sonar-project.properties
.gitattributes
.env.example
ci/docker-compose.yml
ci/jenkins/{Dockerfile, plugins.txt, casc.yaml}
ci/sonar-init/{Dockerfile, provision.sh}
gateway/Dockerfile
observability/compose.yml
observability/prometheus/{Dockerfile, prometheus.yml, alerts.yml}
observability/loki/{Dockerfile, loki.yml}
observability/alloy/{Dockerfile, config.alloy}
observability/grafana/{Dockerfile, provisioning/…, dashboards/*.json}
backend/app/core/logging.py
backend/.coveragerc
```

**Modified**

| File | Change |
|---|---|
| `backend/app/core/app_factory.py` | Logging setup, request middleware, `/metrics`. |
| `backend/requirements.txt` | UTF-8; `prometheus-fastapi-instrumentator`. |
| `gateway/nginx.conf` | JSON access log; internal `stub_status`. |
| `docker-compose.yml` | Include observability; `SERVICE_NAME`/`LOG_LEVEL`; gateway image build; `--no-access-log`. |
| `.gitignore` | §9. |
| `README.md` | §11. |
| `docs/architecture/MICROSERVICES_MIGRATION_PLAN.md` | Logging and observability moved from future work to implemented; link to this document. |

No routers, services, schemas, models or migrations change.

---

## 13. Implementation order

1. Structured logging and metrics in the services; test suite stays green.
2. Observability stack and Grafana provisioning; verify targets, logs and dashboards.
3. Gateway image, JSON access logs, nginx exporter.
4. CI stack: Jenkins image + JCasC, SonarQube, `sonar-init`.
5. `Jenkinsfile`, `sonar-project.properties`, `docker-compose.ci.yml`, `.gitattributes`, `.gitignore`, `.env.example`.
6. Push to `feature/cicd` and run the pipeline end to end: tests → SonarQube → quality gate → build → deploy → seed.
7. README and architecture document updates.
