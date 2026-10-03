import base64
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pages import pv_forecasting
from services import cooling_demand_service as cooling
from services import forecasting_service as pv
from services.dataset_service import list_system_dataset_paths
from services.preprocessing_service import export_preprocessing_artifacts
from services.runtime_service import DATA_ROOT


@pytest.fixture(scope="module")
def artifact():
    paths, pipeline = export_preprocessing_artifacts(list_system_dataset_paths()[0].name, {})
    assert len(pipeline.dataframe) >= 200
    metadata = json.loads(Path(paths["json_path"]).read_text(encoding="utf-8"))
    return metadata["artifact_id"]


@pytest.mark.parametrize("model", list(pv.MODEL_SPECS))
def test_pv_train_predict_download_and_restore(artifact, model):
    if not pv.model_availability().get(model):
        pytest.skip(f"{model} is optional and not installed")
    info = pv.train_model({
        "artifact_id": artifact, "horizons": [5], "models": [model],
        "model_settings": {model: {"n_estimators": 8, "iterations": 8, "epochs": 1,
                                  "max_training_rows": 1000}},
    })
    assert info["model_token"] in {x["value"] for x in pv.list_trained_models()}
    frame = pv._load_artifact_frame(pv.get_artifact(artifact))
    timestamp = frame.iloc[-30]["_ts"].isoformat()
    result = pv.predict_trained_model(info["model_token"], {"timestamp": timestamp})
    value = result["results"][model]["records"][0]["pred_5m"]
    assert value is not None and np.isfinite(value)
    download, _ = pv_forecasting.save_pv_model(1, info)
    assert download["base64"] and len(base64.b64decode(download["content"])) > 100
    # A fresh Python process proves restore works beyond the in-process cache,
    # including PyTorch's formerly local (unpicklable) LSTM class.
    code = (
        "import json, wsgi; from services.forecasting_service import predict_trained_model; "
        f"r=predict_trained_model({info['model_token']!r}, {{'timestamp': {timestamp!r}}}); "
        f"print(json.dumps(r['results'][{model!r}]['records'][0]['pred_5m']))"
    )
    completed = subprocess.run([sys.executable, "-c", code], cwd=Path(__file__).resolve().parents[1],
                               capture_output=True, text=True, check=True)
    assert float(completed.stdout.strip().splitlines()[-1]) == pytest.approx(value)
    curve = pv.predict_trained_model_range(info["model_token"], {
        "start": timestamp, "end": (pd.Timestamp(timestamp) + pd.Timedelta(minutes=15)).isoformat(),
        "horizons": [5],
    })
    assert len(curve["results"][model]["records"]) == 4


@pytest.mark.parametrize("model", list(cooling.FORECAST_MODEL_NAMES))
def test_cooling_backtest_and_export(model):
    if not cooling.model_availability().get(model):
        pytest.skip(f"{model} is optional and not installed")
    source = cooling.list_cooling_sources()[0]
    df = cooling._load_m3_module().load_dataset(source.path)
    result = cooling.run_cooling_backtest({
        "source_id": source.source_id, "source_type": "system", "system_id": 6,
        "profile_id": "lahore_dc_01", "horizons": [10], "models": [model],
        "start": str(df.iloc[-576]["_ts"]), "end": str(df.iloc[-1]["_ts"]),
        "model_settings": {model: {"n_estimators": 8, "iterations": 8, "epochs": 1,
                                  "max_training_rows": 1000}},
        "steady_state_only": False, "auto_calibrate": False,
    })
    payload = result.get("results", {}).get(model, result)
    records = payload["records"]
    assert records and result["metrics"]
    assert any(np.isfinite(r["pred_10m"]) for r in records if r.get("pred_10m") is not None)
    first = cooling.export_cooling_result(result)
    second = cooling.export_cooling_result(result)
    assert first["forecast_csv"] != second["forecast_csv"]
    assert all(Path(path).is_file() for path in first.values())


def test_backup_restore_keeps_model_and_data(artifact, tmp_path):
    info = pv.train_model({"artifact_id": artifact, "models": ["extra_trees"], "horizons": [5],
                           "model_settings": {"extra_trees": {"n_estimators": 5}}})
    frame = pv._load_artifact_frame(pv.get_artifact(artifact))
    timestamp = frame.iloc[-30]["_ts"].isoformat()
    archive = shutil.make_archive(str(tmp_path / "backup"), "gztar", DATA_ROOT)
    restored = tmp_path / "restored"
    shutil.unpack_archive(archive, restored)
    environment = dict(os.environ, S2COOL_DATA_DIR=str(restored))
    code = (
        "import wsgi; from services.forecasting_service import predict_trained_model; "
        f"r=predict_trained_model({info['model_token']!r}, {{'timestamp': {timestamp!r}}}); "
        "assert r['results']['extra_trees']['records'][0]['pred_5m'] is not None"
    )
    subprocess.run([sys.executable, "-c", code], cwd=Path(__file__).resolve().parents[1],
                   env=environment, check=True, capture_output=True, text=True)
