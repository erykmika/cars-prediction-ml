---
name: "model-prediction-validation"
description: "Validates price prediction machine learning model used in the API"

---


# Model Prediction Validation Skill

## Overview
This skill checks that the price predictionmachine learning model used in the API is usable and produces reasonable reliable predictions.

## Prerequisites
- a built docker image of the API (using the Dockerfile at api/Dockerfile)
- a running container of the API (using the image built above)

Additional (optional) quick prerequisites for offline validation:
- a local Python environment with `joblib`, `pandas`, `numpy`, and `scikit-learn` installed
- access to the trained artifact file (example: `api/models/poland_used_cars_linear_regression.joblib`) and training CSV (example: `training/data/data.csv`)

## Step by step guide
1. query the API at the healthcheck endpoint to ensure the model is loaded and ready (http://localhost:8000/health)
2. query the API at the prediction endpoint with a payload of the form given in `api/README.md` containing a random record from the dataset used to train the model, and check that the response is a valid prediction (i.e., -+~10% of the actual price).

## Fast offline validation script

The following Python script was used to validate the saved model artifact quickly without starting the container. It loads the artifact, selects a preprocessed example row from the training CSV (applying the same numeric coercion used in training), runs a prediction, applies any output transform (such as `pow10`) and reports the absolute and percentage error.

Usage (from repository root):

```bash
# from the project root
python -m venv .venv
source .venv/bin/activate
pip install joblib pandas numpy scikit-learn
python .agents/skills/model-prediction-validation/validate_model.py
```

Script: `.agents/skills/model-prediction-validation/validate_model.py`

```python
from pathlib import Path
import json
import numpy as np
import pandas as pd
import joblib

ROOT = Path(__file__).resolve().parents[3]
DATA_CANDIDATES = [
	ROOT / 'training' / 'data' / 'data.csv',
	ROOT / 'data' / 'data.csv',
	ROOT / 'training' / 'fetched' / 'data.csv',
]
MODEL_CANDIDATES = [
	ROOT / 'api' / 'models' / 'poland_used_cars_linear_regression.joblib',
	ROOT / 'models' / 'poland_used_cars_linear_regression.joblib',
	ROOT / 'training' / 'models' / 'poland_used_cars_linear_regression.joblib',
]

data_path = next((p for p in DATA_CANDIDATES if p.exists()), None)
model_path = next((p for p in MODEL_CANDIDATES if p.exists()), None)

if data_path is None or model_path is None:
	raise FileNotFoundError(f"Missing data or model. Searched: {DATA_CANDIDATES}, {MODEL_CANDIDATES}")

NUMERIC_FEATURE_COLUMNS = {'mileage', 'engine_capacity', 'year'}
NUMERIC_COLUMN_UNITS = {'mileage': r"km", 'engine_capacity': r"cm3|cm³"}
FEATURES_TO_DROP = {'voivodeship', 'city'}
TARGET = 'price_in_pln'

def coerce_numeric_series(series: pd.Series, column_name: str) -> pd.Series:
	if pd.api.types.is_numeric_dtype(series):
		return pd.to_numeric(series, errors='coerce')

	unit_pattern = NUMERIC_COLUMN_UNITS.get(column_name)
	text = series.astype('string').str.strip()
	if unit_pattern is not None:
		text = text.str.replace(rf"\s*(?:{unit_pattern})\s*$", "", regex=True, case=False)

	cleaned = (
		text.str.replace(r"\s+", "", regex=True)
		.str.replace(r"[^\d,.\-]", "", regex=True)
		.str.replace(",", ".", regex=False)
		.replace("", np.nan)
	)
	return pd.to_numeric(cleaned, errors='coerce')

df = pd.read_csv(data_path)
if TARGET not in df.columns:
	raise ValueError('Expected target column price_in_pln in dataset')

df = df.dropna(subset=[TARGET])
try:
	df = df[df[TARGET] > 0]
except Exception:
	pass

for col in NUMERIC_FEATURE_COLUMNS.intersection(df.columns):
	df[col] = coerce_numeric_series(df[col], column_name=col)

features_df = df.drop(columns=[TARGET] + [c for c in FEATURES_TO_DROP if c in df.columns], errors='ignore')
sample = features_df.dropna(how='any').sample(n=1, random_state=42).iloc[0]
actual_price = float(df.loc[sample.name, TARGET])

artifact = joblib.load(model_path)
if isinstance(artifact, dict) and 'model' in artifact:
	pipeline = artifact['model']
	feature_columns = artifact.get('feature_columns')
	output_transform = artifact.get('output_transform')
else:
	pipeline = artifact
	feature_columns = None
	output_transform = None

if feature_columns is not None:
	features = {c: sample[c] for c in feature_columns}
	X = pd.DataFrame([features], columns=feature_columns)
else:
	feature_cols = [c for c in features_df.columns]
	X = pd.DataFrame([sample[feature_cols].astype(object)])

raw_pred = pipeline.predict(X)
raw_value = np.asarray(raw_pred).ravel()[0]
if output_transform == 'pow10':
	pred_price = float(np.power(10, raw_value))
else:
	pred_price = float(raw_value)

pct_error = abs(pred_price - actual_price) / actual_price * 100

result = {
	'actual_price': actual_price,
	'pred_price': pred_price,
	'pct_error': pct_error,
	'output_transform': output_transform,
	'within_10pct': pct_error <= 10.0,
}
print(json.dumps(result, indent=2))
```

## Tips to reduce agent run-time

- Prefer offline validation (script above) rather than building and starting the Docker image when you only need a quick sanity check.
- Keep the model artifact at `api/models/...` and the training CSV at `training/data/data.csv` so the script finds them by default.
- If you want to validate the running service instead, start the app locally with `uvicorn app.main:app --reload` and check `/health` and `/predict` as described in `api/README.md`.
- Cache a small subset of cleaned rows (CSV or parquet) for the agent to pick examples from quickly (e.g., `training/data/sample_clean.csv`).

## Expected output

The script prints a JSON object with `actual_price`, `pred_price`, `pct_error`, and `within_10pct` (boolean). Use this to decide whether the model is producing reasonable predictions.

