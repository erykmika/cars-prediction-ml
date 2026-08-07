#!/bin/sh
set -e

TRAINED_MODEL="${TRAINED_MODEL:-/training/models/poland_used_cars_linear_regression.joblib}"
API_MODEL_DIR="${API_MODEL_DIR:-models}"

echo "Copying trained model..."
mkdir -p "$API_MODEL_DIR"
cp "$TRAINED_MODEL" "$API_MODEL_DIR/poland_used_cars_linear_regression.joblib"

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
exec "$@"