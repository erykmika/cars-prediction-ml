import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.train import build_cross_validation_metrics


def test_build_cross_validation_metrics_summarizes_fold_scores() -> None:
    cv_results = {
        "test_mae": [-1.0, -2.0, -3.0],
        "test_rmse": [-1.5, -2.5, -3.5],
        "test_r2": [0.8, 0.7, 0.6],
    }

    metrics = build_cross_validation_metrics(cv_results)

    assert metrics["mae"]["mean"] == pytest.approx(2.0)
    assert metrics["mae"]["std"] == pytest.approx(1.0)
    assert metrics["rmse"]["mean"] == pytest.approx(2.5)
    assert metrics["rmse"]["std"] == pytest.approx(1.0)
    assert metrics["r2"]["mean"] == pytest.approx(0.7)
    assert metrics["r2"]["std"] == pytest.approx(0.1)
