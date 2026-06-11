# FastAPI Large Application Template 🚀

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)

A production-ready FastAPI template designed for building secure, scalable APIs with modern best practices baked in. This template provides a robust foundation for enterprise-grade applications, featuring essential security measures, performance optimizations, and maintainable architecture patterns out of the box.

## Features ✨

- **JWT Authentication** — login, logout (token blacklist) and refresh-token rotation 🔒
- **Argon2id Password Hashing** via `pwdlib` 🔑
- **Custom Rate Limiting** per user/service, declared as a route dependency ⏱️
- **Unified Logging** (UVICORN + GUNICORN) 📝
- **Redis Connection Pooling** (Async) with fail-open strategy 🧠
- **PostgreSQL Connection Pooling** (Async) with health checks 🐘
- **Standardized API Responses** with centralized exception handlers 📦
- **Typed Settings** via `pydantic-settings` (fail-fast validation) ⚙️
- **Alembic for Database Migrations** 🗄️
- **Modern Package Management with `uv`** ⚡
- **One-command Local Stack** — `make up` (app + Postgres + Redis) 🐳
- **Kubernetes Manifests** — probes, security context, NetworkPolicy, HPA ☸️
- **OpenTelemetry Observability** — metrics, traces, Golden Signals dashboards (Prometheus + Grafana + Tempo) 📊

## Observability 📊

This template includes a **production-grade OpenTelemetry observability setup** designed for real-world systems:

- Automatic FastAPI instrumentation
- Distributed tracing with Tempo
- Golden Signals dashboards in Grafana
- Prometheus metrics via OpenTelemetry
- Custom application & rate-limiter visibility

### Observability Stack

[![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-FFFFFF?style=for-the-badge&logo=opentelemetry&logoColor=black)](https://opentelemetry.io/)
[![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=Prometheus&logoColor=white)](https://prometheus.io/)
[![Grafana](https://img.shields.io/badge/grafana-%23F46800.svg?style=for-the-badge&logo=grafana&logoColor=white)](https://grafana.com/)
[![Grafana Tempo](https://img.shields.io/badge/Tempo-000000?style=for-the-badge&logo=grafana&logoColor=white)](https://grafana.com/oss/tempo/)


👉 **All observability details live here:**
📄 [docs/OBSERVABILITY.md](docs/OBSERVABILITY.md)

## Tech Stack 🛠️

| Component              | Technology                          |
|------------------------|-------------------------------------|
| Framework              | FastAPI 0.121+                      |
| Database               | PostgreSQL 14+                      |
| Cache                  | Redis 6+                            |
| ORM                    | SQLAlchemy 2.0 (async, asyncpg)     |
| Migrations             | Alembic                             |
| Configuration          | pydantic-settings                   |
| Authentication         | JWT (OAuth2 Password Bearer)        |
| Password Hashing       | Argon2id (`pwdlib`)                 |
| Rate Limiting          | Redis-backed Custom Implementation  |
| Package Manager        | `uv` (fast Python installer)        |
| Containerization       | Docker + docker-compose             |
| Orchestration          | Kubernetes (manifests in `k8s/`)    |
| Observability          | OpenTelemetry                       |
| Testing                | pytest, fakeredis, hypothesis       |

## Project Structure 🌳

The repository follows a **layered architecture** — each request flows
`api → services → crud → models`, with `schemas` for I/O validation. This keeps
HTTP concerns, business logic, and persistence cleanly separated and easy to
test in isolation.

```
app/
├── api/            # Routers + request dependencies (user, todo, health)
├── services/       # Business logic (orchestrates crud + auth)
├── crud/           # Async SQLAlchemy data-access functions
├── models/         # SQLAlchemy ORM models
├── schemas/        # Pydantic request/response schemas
├── core/           # Settings, database, auth, exceptions, middleware, logging
├── utils/          # Rate limiter dependency
├── observability/  # OpenTelemetry telemetry, metrics, instrumentation
├── alembic/        # Migration environment & versions
└── main.py         # App factory, middleware wiring, exception handlers, lifespan

k8s/                # Kubernetes manifests (deployment, service, HPA, NetworkPolicy, jobs)
docker/observability/  # Local Grafana/Tempo/Prometheus/OTel collector stack
docs/               # Observability guide, dashboards, screenshots
tests/              # unit / integration / e2e suites (pytest, fakeredis, hypothesis)
docker-compose.yml  # One-command local stack (app + postgres + redis)
Dockerfile          # Canonical multi-stage image (lockfile-pinned)
```

---

## Key Implementations 🔑

These patterns are the reason the template exists. Rather than paste code that
drifts from the source, each links to the file that owns it.

| Concern | Where it lives | What to look at |
|---------|----------------|-----------------|
| **Typed settings** | [app/core/settings.py](app/core/settings.py) | `pydantic-settings` tree, validated and fail-fast (e.g. rejects `CORS=*` with credentials in prod) |
| **Async DB pooling** | [app/core/database.py](app/core/database.py) | `create_async_engine` + `async_sessionmaker`, pre-ping, recycle; pool sizes come from settings |
| **Redis pool + lifespan** | [app/main.py](app/main.py) | Connection pool, startup health checks, graceful `engine.dispose()` on shutdown |
| **JWT auth** | [app/core/auth.py](app/core/auth.py), [app/api/deps.py](app/api/deps.py) | Access/refresh token types, `get_current_user`, blacklist check |
| **Auth flows** | [app/services/user_service.py](app/services/user_service.py) | Register / login / logout / refresh-token rotation |
| **Rate limiting** | [app/utils/rate_limiter.py](app/utils/rate_limiter.py) | `RateLimit(...)` dependency — declared in the route signature, fail-open on Redis errors |
| **Centralized errors** | [app/main.py](app/main.py), [app/core/exceptions.py](app/core/exceptions.py) | `AppError` handlers map domain errors to status codes; routers stay thin |
| **Standardized responses** | [app/core/schemas.py](app/core/schemas.py) | `ApiResponse` / `PaginatedApiResponse` generics |
| **Logging** | [app/core/logging_config.py](app/core/logging_config.py) | Unified Uvicorn/Gunicorn formatter with correlation ID |
| **Observability** | [app/observability/](app/observability/) | OpenTelemetry tracing + metrics; see [docs/OBSERVABILITY.md](docs/OBSERVABILITY.md) |

Every endpoint returns the same envelope:

```json
{ "status": "success", "message": "...", "data": { ... } }
```

…and errors are normalized by the handlers in `main.py`:

```json
{ "status": "error", "message": "Validation Failed", "errors": [ ... ] }
```

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- Docker (optional, but the fastest way to run the full stack)

---

### Quickstart (Docker Compose) 🐳

The fastest path — builds the app image and starts the app, PostgreSQL, and
Redis together. Migrations run automatically on container start.

```bash
make up      # build + start app + postgres + redis (detached)
make logs    # follow the app logs
make down    # stop and remove the stack
```

Then open <http://localhost:8000/docs>. To also run the observability stack
(Grafana/Tempo/Prometheus/OTel), use `make up-observability`.

---

### Installation (local Python)

```bash
git clone https://github.com/akhil2308/fastapi-large-app-template.git
cd fastapi-large-app-template

# Install uv (if not already installed)
pip install uv

# Sync dependencies and create virtual environment
# This installs all packages defined in pyproject.toml
uv sync --all-extras

# Install Git Hooks
# This ensures code quality checks run automatically on commit
uv run pre-commit install
```

---

## Using Makefile

This project includes a Makefile with convenient commands. Run `make help` to see all available targets.

```bash
# Show all available commands
make help

# Install dependencies and setup git hooks
make install

# Development server
make dev

# Production server
make prod

# Run tests
make test

# Database migrations
make migrate
make migrate-create MSG="your migration message"

# Code quality
make check-env
make lint
make format
make typecheck

# Full CI pipeline
make ci

# Local Docker stack (app + postgres + redis)
make up
make down
make logs

# Observability stack (Grafana/Tempo/Prometheus/OTel)
make up-observability
make down-observability

# Clean generated files
make clean
```

---

### Configuration

#### Set environment variables

```bash
cp .env.example .env
# Fill in DB, Redis, JWT, and other values
```

---

## Alembic Commands (Migrations)

**Generate new migration:**

```bash
uv run alembic -c app/alembic.ini revision --autogenerate -m "message"
```

**Apply migrations:**

```bash
uv run alembic -c app/alembic.ini upgrade head
```

---

### Running

**Development:**

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Production:**

```bash
./run.sh  # Applies migrations, then starts Gunicorn with uvicorn-worker
```

---

## Docker 🐳

A single canonical multi-stage [Dockerfile](Dockerfile) is used by both
docker-compose and Kubernetes. It installs dependencies straight from `uv.lock`
with `uv sync --frozen` (so the image can never drift from the committed lock),
pins the Python base image, and runs as a non-root user.

```bash
docker build -t fastapi-large-app-template .
```

---

## Kubernetes ☸️

Manifests live in [k8s/](k8s/) — namespace, ConfigMap/Secret, Deployment,
Service, HPA, PodDisruptionBudget, a default-deny NetworkPolicy, and a
migration Job. The Deployment ships with startup/readiness/liveness probes, a
hardened security context, and `automountServiceAccountToken: false`.

```bash
# 1. Build and push your image, then set it in k8s/app/deployment.yaml
#    and k8s/jobs/migration.yaml.
# 2. Fill in k8s/app/secret.yaml (JWT_SECRET_KEY, DB/Redis passwords) and
#    review k8s/app/configmap.yaml (ALLOWED_HOSTS, CORS_ORIGINS, OTEL endpoint).
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/app/
kubectl apply -f k8s/jobs/migration.yaml
```

See [k8s/README.md](k8s/README.md) for the full walkthrough.

---

## Code Standards & Quality 🛡️

This project enforces code quality using **Ruff** (linter/formatter) and **Mypy** (static type checker).

### Manual Checks

**1. Linting & Formatting (Ruff)**

```bash
# See what code Ruff wants to fix (Dry Run)
uv run ruff check .

# Actually fix the code (Auto-formatting & Import sorting)
uv run ruff check . --fix
uv run ruff format .
```

**2. Static Type Checking (Mypy)**

```bash
# Check for type errors
uv run mypy .
```

> **Note:** 🔒 A **pre-commit hook** is configured. When you attempt to `git commit`, these checks will automatically run to ensure no bad code is pushed to the repository.

---

## API Documentation 📚

Access interactive docs after starting server:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI:** `http://localhost:8000/openapi.json`

## Contributing

See [CONTRIBUTORS.txt](CONTRIBUTORS.txt) for contribution guidelines and code of conduct.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.
