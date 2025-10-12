import importlib
import json
import os
import pytest

@pytest.mark.skipif(not os.path.isdir(os.path.join(os.getcwd(), "datasets")), reason="datasets missing")
def test_evaluation_metrics_exist():
    # Example quality gates. Replace with real metrics from app pipeline.
    expected_metrics = {"cagr", "sharpe", "drawdown", "win_rate"}
    metrics_path = os.path.join("outputs", "metrics_example.json")
    if os.path.exists(metrics_path):
        with open(metrics_path) as f:
            metrics = set(json.load(f).keys())
        missing = expected_metrics - metrics
        assert not missing, f"Missing metrics: {missing}"
    else:
        # Not failing if file not yet produced; acts as a template.
        pytest.skip("metrics_example.json not found; generate via pipeline to enable this check.")