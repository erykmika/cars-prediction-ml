# Cars Prediction ML

Machine learning project for training and serving Poland used-car price predictions.

The repository is split into two independent parts:

- `training/` trains a scikit-learn `LinearRegression` pipeline on the Kaggle Poland used cars
  offers dataset.
- `api/` serves the trained model through a FastAPI prediction service.

## Project Layout

```text
cars-prediction-ml/
├── Makefile
├── docker-compose.yml
├── railway.json
├── api/
│   ├── app/
│   ├── alembic/
│   ├── models/
│   ├── tests/
│   ├── Dockerfile
│   ├── Makefile
│   └── docker-entrypoint.sh
└── training/
    ├── data/
    ├── metrics/
    ├── models/
    ├── src/
    ├── tests/
    └── Makefile
```

## Development

Meaningful changes are introduced by submitting pull requests.  
These are reviewed using an AI pipeline which is scripted using `scripts/ai_review.py`.

## Run full pipeline (training a model + running the API with the model loaded)
```bash
make run-full-pipeline
```

## Training Flow

```bash
cd training
cp .env.example .env
make all
```

`make all` downloads the Kaggle dataset into `training/data/fetched/` and trains the model into
`training/models/poland_used_cars_linear_regression.joblib`. To train against a custom CSV, pass
`DATA_PATH=/path/to/your/file.csv` to `make`. See `training/README.md` for details.

The training target column is `price_in_pln`. All remaining dataset columns except `voivodeship`
and `city` are used as features.

## API Flow

```bash
cd api
make test
make lint
make docker-compose-up
```

`make docker-compose-up` builds the API image and starts it together with PostgreSQL. On startup
the container entrypoint copies the trained artifact from `training/models/` into the API service
and runs the Alembic migrations. The API loads `models/poland_used_cars_linear_regression.joblib`
and exposes:

- `GET /health` (public)
- `POST /auth/login` - Obtain access/refresh tokens
- `POST /auth/refresh` - Refresh access token
- `GET /auth/me` - Get current user info
- `POST /predict` (requires authentication)

Each prediction is persisted to the `predictions` table in PostgreSQL.

Example authentication and prediction flow:

```bash
# 1. Login to get tokens
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"CARS_PREDICTION_USER","password":"123"}'

# 2. Use access token for prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"features":{"brand":"alfa-romeo","model":"Alfa Romeo 156 2.5 V6 Distinctive","mileage":195000,"gearbox":"manual","engine_capacity":1598,"fuel_type":"Benzyna","year":1998}}'

# 3. Refresh access token when expired
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<refresh_token>"}'
```
