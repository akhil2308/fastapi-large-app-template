"""Gunicorn development config file"""
import os

wsgi_app = "app.main:app"

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"

# Worker settings
workers = int(os.getenv("WORKERS", 1))
worker_class = "uvicorn.workers.UvicornWorker"

# Bind address
bind = "0.0.0.0:8000"

# Reload only for development (disabled in production)
reload = False