# Training

Training code for a linear regression model based on the Kaggle
[Poland Used Cars Offers](https://www.kaggle.com/datasets/wspirat/poland-used-cars-offers)
dataset.

## Dataset

Create a local `.env` file for Kaggle authentication:

```bash
cp .env.example .env
```

Then set `KAGGLE_API_TOKEN` in `.env`.

Download the latest dataset version through the Kaggle connector:

```bash
make fetch-data
```

The connector prints the local Kaggle cache path returned by `kagglehub`. You can then either pass
the downloaded CSV path directly to training:

```bash
make train DATA_PATH=/path/from/kagglehub/file.csv
```

or place/copy the CSV at:

```text
training/data/poland_used_cars.csv
```

If your file has a different name, pass `DATA_PATH` to `make`.

## Train

```bash
make all
```

This trains the model into `training/models/poland_used_cars_linear_regression.joblib` and then
copies it to `api/models/poland_used_cars_linear_regression.joblib` for the FastAPI service.

The trainer expects the target column to be `price_in_pln`, keeps all other columns as features,
builds a numeric/categorical preprocessing pipeline, and saves model metadata with the artifact.
