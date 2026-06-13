# Canonical multi-stage image for both local (docker-compose) and Kubernetes.
# Pin the base image to a specific patch release for reproducible builds.
ARG PYTHON_IMAGE=python:3.11.9-slim

# =============================================================================
# Stage 1 — builder
# Installs uv and resolves dependencies straight from uv.lock into an isolated
# virtual environment at /opt/venv. Only that venv is carried into the runtime
# stage, so build tools never reach the final image.
# =============================================================================
FROM ${PYTHON_IMAGE} AS builder

# C build tools required by some Python packages (e.g. psycopg2-binary fallback).
RUN apt-get update && \
    apt-get install -y python3-dev build-essential curl --no-install-recommends && \
    apt-get clean && rm -rf /tmp/* /var/tmp/* && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Install uv — a fast Rust-based Python package manager.
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

# Build into a fixed venv path so the runtime stage can copy it verbatim.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv

# Install only third-party deps first (cached unless the lockfile changes).
# --frozen fails the build if uv.lock is out of sync with pyproject.toml, so
# the image can never silently drift from the committed lock.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy the source and install the project itself into the same venv.
COPY . .
RUN uv sync --frozen --no-dev


# =============================================================================
# Stage 2 — runtime
# Minimal image containing only the pre-built venv and application source.
# Runs as a non-root user for security hardening.
# =============================================================================
FROM ${PYTHON_IMAGE} AS runtime

# Dedicated non-root user (uid 1000); --no-log-init avoids a known Docker issue.
RUN useradd --create-home --no-log-init --uid 1000 appuser

COPY --from=builder /opt/venv /opt/venv

COPY --chown=appuser:appuser app/           /app/app/
COPY --chown=appuser:appuser run.sh         /app/run.sh
COPY --chown=appuser:appuser pyproject.toml /app/pyproject.toml

WORKDIR /app

# Resolve installed executables (gunicorn, alembic, …) from the venv.
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

RUN chmod +x /app/run.sh

USER appuser

EXPOSE 8000

# Serve with Gunicorn using the maintained uvicorn-worker package (the in-tree
# uvicorn.workers.UvicornWorker is deprecated upstream). A single worker is the
# safe default for Kubernetes where scaling happens at the pod level.
CMD ["gunicorn", \
     "--workers", "1", \
     "--worker-class", "uvicorn_worker.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--graceful-timeout", "45", \
     "--log-level", "info", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "app.main:app"]
