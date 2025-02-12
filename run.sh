#!/bin/bash -e

python -V

# Running server
gunicorn -c gunicorn_conf.py
