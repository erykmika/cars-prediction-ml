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

The CSV is downloaded into `training/data/fetched/data.csv`, which is the default `DATA_PATH` used
by the `train` target. If you already have your own CSV, copy it into the repo and point the
pipeline at it:

```bash
make all DATA_PATH=/path/to/your/file.csv
```

## Train

`make all` downloads the dataset and trains the model:

```bash
make all
```

The artifact is saved to `training/models/poland_used_cars_linear_regression.joblib`, with metrics
written to `training/metrics/`. To train only (skipping the download), run:

```bash
make train DATA_PATH=data/fetched/data.csv
```

The trainer expects the target column to be `price_in_pln`, keeps all remaining columns except
`voivodeship` and `city` as features, builds a numeric/categorical preprocessing pipeline, and
saves model metadata with the artifact.

When the API is started with Docker Compose, the container entrypoint copies this artifact from
`training/models/` into the running API service.
