import argparse
import json
import logging
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

TARGET_COLUMN = "price_in_pln"
NUMERIC_FEATURE_COLUMNS = frozenset({"mileage", "engine_capacity", "year"})
NUMERIC_COLUMN_UNITS = {
    "mileage": r"km",
    "engine_capacity": r"cm3|cm³",
}
LOGGER = logging.getLogger(__name__)
FEATURES_TO_DROP = frozenset({"voivodeship", "city"})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a Poland used cars linear regression model."
    )
    parser.add_argument("--data-path", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--max-rows", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    args = parse_args()
    data = load_dataset(args.data_path, max_rows=args.max_rows)
    features, target = prepare_training_data(data, TARGET_COLUMN)

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=args.test_size,
        random_state=args.random_state,
    )

    # scale output feature logarithmically
    def _map_func(y):
        math.log10(y)

    y_train: pd.Series = y_train.map(func=_map_func)
    y_test: pd.Series = y_test.map(func=_map_func)

    pipeline = build_pipeline(features)
    pipeline.fit(x_train, y_train)

    predictions = pipeline.predict(x_test)
    metrics = build_metrics(y_test, predictions)
    artifact = {
        "model": pipeline,
        "model_type": "linear_regression",
        "model_version": datetime.now(UTC).strftime("%Y%m%d%H%M%S"),
        "feature_columns": features.columns.tolist(),
        "target_column": TARGET_COLUMN,
        "metrics": metrics,
        "trained_at": datetime.now(UTC).isoformat(),
    }

    args.model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, args.model_path)
    write_metrics(args.model_path, metrics)

    LOGGER.info(f"Saved model artifact to {args.model_path}")
    LOGGER.info(f"{json.dumps(metrics, indent=2, sort_keys=True)}")


def load_dataset(data_path: Path, *, max_rows: int | None) -> pd.DataFrame:
    if not data_path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {data_path}. Download the Kaggle CSV into training/data "
            "or pass DATA_PATH=/path/to/file.csv."
        )

    return pd.read_csv(data_path, nrows=max_rows)


def prepare_training_data(data: pd.DataFrame, target_column: str) -> tuple[pd.DataFrame, pd.Series]:
    if target_column not in data.columns:
        raise ValueError(f"Target column '{target_column}' is not present in the dataset.")

    working_data = data.copy()
    working_data[target_column] = coerce_numeric_series(
        working_data[target_column],
        column_name=target_column,
    )
    working_data = working_data.dropna(subset=[target_column])
    working_data = working_data[working_data[target_column] > 0]
    working_data = working_data.dropna(axis=1, how="all")

    features = working_data.drop(columns=[target_column] + list(FEATURES_TO_DROP))
    target = working_data[target_column]

    if features.empty:
        raise ValueError("No feature columns remain after preprocessing.")

    return normalize_feature_values(features), target


def normalize_feature_values(features: pd.DataFrame) -> pd.DataFrame:
    normalized = features.copy()

    for column in NUMERIC_FEATURE_COLUMNS.intersection(normalized.columns):
        normalized[column] = coerce_numeric_series(
            normalized[column],
            column_name=column,
        )

    return normalized


def coerce_numeric_series(series: pd.Series, *, column_name: str) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")

    unit_pattern = NUMERIC_COLUMN_UNITS.get(column_name)
    text = series.astype("string").str.strip()
    if unit_pattern is not None:
        text = text.str.replace(rf"\s*(?:{unit_pattern})\s*$", "", regex=True, case=False)

    cleaned = (
        text.str.replace(r"\s+", "", regex=True)
        .str.replace(r"[^\d,.\-]", "", regex=True)
        .str.replace(",", ".", regex=False)
        .replace("", np.nan)
    )
    return pd.to_numeric(cleaned, errors="coerce")


def build_pipeline(features: pd.DataFrame) -> Pipeline:
    numeric_features = features.select_dtypes(include=["number", "bool"]).columns.tolist()
    categorical_features = [column for column in features.columns if column not in numeric_features]

    LOGGER.info(f"numeric_features={numeric_features}, categorical_features={categorical_features}")

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "encoder",
                OneHotEncoder(
                    handle_unknown="ignore",
                    min_frequency=20,
                    sparse_output=True,
                ),
            ),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, numeric_features),
            ("categorical", categorical_pipeline, categorical_features),
        ],
        remainder="drop",
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", LinearRegression()),
        ]
    )


def build_metrics(y_true: pd.Series, predictions: np.ndarray) -> dict[str, float]:
    mse = mean_squared_error(y_true, predictions)
    return {
        "mae": float(mean_absolute_error(y_true, predictions)),
        "rmse": float(np.sqrt(mse)),
        "r2": float(r2_score(y_true, predictions)),
    }


def write_metrics(model_path: Path, metrics: dict[str, Any]) -> None:
    metrics_path = Path("metrics") / f"{model_path.stem}.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
