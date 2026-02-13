#!/bin/bash -e

python -V

echo "Running database migrations..."
alembic -c app/alembic.ini upgrade head

echo "Starting FastAPI server..."
gunicorn \
    --workers 1 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    app.main:app
