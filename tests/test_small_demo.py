import pytest

from services import cooling_demand_service as cooling
from services import forecasting_service as pv
from services.runtime_service import limit_demo_settings


def test_server_caps_cannot_be_removed_by_request(monkeypatch):
    monkeypatch.setenv("S2COOL_SMALL_DEMO", "1")
    settings = {"max_training_rows": 0, "n_estimators": 100000, "max_depth": -1}
    assert limit_demo_settings("extra_trees", settings) == {
        "max_training_rows": 2000, "n_estimators": 30, "max_depth": 6,
    }
    assert settings["n_estimators"] == 100000
    with pytest.raises(ValueError, match="disabled"):
        limit_demo_settings("lstm", {})
    assert not pv.model_availability()["lstm"]
    assert not cooling.model_availability()["lstm"]


def test_small_demo_limits_are_recorded_on_pv_model(monkeypatch):
    monkeypatch.setenv("S2COOL_SMALL_DEMO", "1")
    from services.dataset_service import list_system_dataset_paths
    from services.preprocessing_service import export_preprocessing_artifacts
    import json
    from pathlib import Path

    paths, _ = export_preprocessing_artifacts(list_system_dataset_paths()[0].name, {})
    artifact = json.loads(Path(paths["json_path"]).read_text())["artifact_id"]
    info = pv.train_model({"artifact_id": artifact, "horizons": [5], "models": ["extra_trees"],
                           "model_settings": {"extra_trees": {"n_estimators": 5000,
                                                              "max_training_rows": 0}}})
    assert info["model_settings"]["extra_trees"]["n_estimators"] == 30
    assert info["model_settings"]["extra_trees"]["max_training_rows"] == 2000


def test_calibration_rejected_before_loading_data(monkeypatch):
    monkeypatch.setenv("S2COOL_SMALL_DEMO", "1")
    with pytest.raises(cooling.CoolingDemandError, match="calibration is disabled"):
        cooling.run_cooling_backtest({"auto_calibrate": True})
