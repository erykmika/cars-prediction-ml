# Cars Prediction ML API

FastAPI service for serving scikit-learn car prediction models.

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

The service expects a trained model at `models/poland_used_cars_linear_regression.joblib` by
default. Override it with
`MODEL_PATH=/path/to/model.pkl`.

## API

Health:

```bash
curl http://localhost:8000/health
```

Prediction:

```bash
 curl -X POST http://localhost:8000/predict \
 -H "Content-Type: application/json" \
 -d '{"features":{"brand":"alfa-romeo","model":"Alfa Romeo 156 2.5 V6 Distinctive","mileage":"195000","gearbox":"manual","engine_capacity":"1598","fuel_type":"Benzyna","year":1998}}'
```

## Docker

```bash
docker build -t cars-prediction-api .
docker run --rm -p 8000:8000 \
  -e MODEL_PATH=models/poland_used_cars_linear_regression.joblib \
  cars-prediction-api
```

## Configuration

See `.env.example` for supported environment variables.
