#!/bin/sh
set -e

API_MODEL_DIR="${API_MODEL_DIR:-models}"

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
exec "$@"