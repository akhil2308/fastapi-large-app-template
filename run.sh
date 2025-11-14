#!/bin/bash -e

python -V

echo "Running database migrations..."
alembic -c app/alembic.ini upgrade head

echo "Starting FastAPI server..."
gunicorn -c gunicorn_config.py
