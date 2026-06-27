# Cars Prediction ML

Machine learning project for training and serving Poland used-car price predictions.

The repository is split into two independent parts:

- `training/` trains a scikit-learn `LinearRegression` pipeline on the Kaggle Poland used cars
  offers dataset.
- `api/` serves the trained model through a FastAPI prediction service.

## Project Layout

```text
cars-prediction-ml/
├── api/
│   ├── app/
│   ├── models/
│   ├── tests/
│   ├── Dockerfile
│   └── Makefile
└── training/
    ├── data/
    ├── models/
    ├── src/
    └── Makefile
```

## Run full pipeline (training a model + running the API with the model loaded)
```bash
run-full-pipeline
```

## Training Flow

```bash
cd training
cp .env.example .env
make fetch-data
make all DATA_PATH=data/data.csv
```

`make all` trains the model and copies the resulting artifact to
`api/models/poland_used_cars_linear_regression.joblib`.

The training target column is `price_in_pln`. All other dataset columns are used as features.

## API Flow

```bash
cd api
make test
make lint
make docker-run
```

The API loads `models/poland_used_cars_linear_regression.joblib` on startup and exposes:

- `GET /health`
- `POST /predict`

Example prediction payload:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"features":{"brand":"alfa-romeo","model":"Alfa Romeo 156 2.5 V6 Distinctive","mileage":"195 000 km","gearbox":"manual","engine_capacity":"1 598 cm3","fuel_type":"Benzyna","city":"Warszawa","voivodeship":"Mazowieckie","year":1998}}'
```
