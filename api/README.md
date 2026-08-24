# Cars Prediction ML API

FastAPI service for serving scikit-learn car prediction models.

## Run Locally

```bash
uv sync --extra dev
uv run uvicorn app.main:app --reload
```

The service expects a trained model at `models/poland_used_cars_linear_regression.joblib` by
default. Override it with
`MODEL_PATH=/path/to/model.pkl`.

The API persists each prediction to a PostgreSQL database. By default it connects to
`postgresql://postgres:postgres@localhost:5432/cars_predictions` (see `.env.example`). Start the
database first with `docker compose -f ../docker-compose.yml up -d db` (from the repository root).

## API

Health (public):

```bash
curl http://localhost:8000/health
```

Authentication:

```bash
# Login to get tokens
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"CARS_PREDICTION_USER","password":"123"}'

# Refresh access token
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<refresh_token>"}'

# Get current user
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer <access_token>"
```

Prediction (requires authentication):

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"features":{"brand":"alfa-romeo","model":"Alfa Romeo 156 2.5 V6 Distinctive","mileage":195000,"gearbox":"manual","engine_capacity":1598,"fuel_type":"Benzyna","year":1998}}'
```

## Docker

The Dockerfile is written against the repository root as the build context:

```bash
# from the repository root
docker build -t cars-prediction-api -f api/Dockerfile .
```

The API requires a PostgreSQL database, so the simplest way to run the full stack (PostgreSQL +
the API) is Docker Compose:

```bash
make docker-compose-up
```

On startup the container entrypoint copies the trained model from `training/models/` and runs the
Alembic migrations before starting the service.

## Configuration

See `.env.example` for supported environment variables.
