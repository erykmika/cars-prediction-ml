# Cars Prediction ML API

FastAPI service for serving scikit-learn car prediction models.

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

The service expects a trained model at `models/model.joblib` by default. Override it with
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
  -d '{"features":[2018,45000,1.6,110,5]}'
```

## Docker

```bash
docker build -t cars-prediction-api .
docker run --rm -p 8000:8000 \
  -e MODEL_PATH=models/model.joblib \
  cars-prediction-api
```

## Configuration

See `.env.example` for supported environment variables.
