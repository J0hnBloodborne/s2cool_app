"""Check the actual sample data and model paths; report time and peak memory."""

import argparse
import json
import os
import platform
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="Use the entire bundled datasets")
    parser.add_argument("--models", default="extra_trees,lstm")
    parser.add_argument("--report", type=Path, default=Path("build/smoke-report.json"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sys.path[:0] = [str(root), str(root / "s2cool_python_app")]
    os.environ["S2COOL_MODEL_THREADS"] = "2"
    for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ.setdefault(variable, "2")
    with tempfile.TemporaryDirectory(prefix="s2cool-smoke-") as temporary:
        os.environ["S2COOL_DATA_DIR"] = temporary
        from services.runtime_service import DATA_ROOT
        import pandas as pd
        if not args.full:
            for path in DATA_ROOT.glob("*/data/*.csv"):
                pd.read_csv(path).head(2880).to_csv(path, index=False)
        import wsgi
        from services import cooling_demand_service as cooling
        from services import forecasting_service as pv
        from services.dataset_service import list_system_dataset_paths
        from services.preprocessing_service import export_preprocessing_artifacts

        # psutil is a dev-only memory sampler. Do not silently invent a reading
        # when it is absent (e.g. a minimal Oracle environment).
        try:
            import psutil
            process = psutil.Process()
        except ImportError:
            process = None
        peak = [process.memory_info().rss if process else None]
        stopped = threading.Event()
        def sample_memory():
            while not stopped.wait(0.1):
                peak[0] = max(peak[0], process.memory_info().rss)
        sampler = threading.Thread(target=sample_memory, daemon=True) if process else None
        if sampler:
            sampler.start()
        report = {"platform": platform.platform(), "architecture": platform.machine(),
                  "python": platform.python_version(), "full_datasets": args.full, "checks": []}
        def check(name, function):
            start = time.perf_counter()
            result = function()
            elapsed = round(time.perf_counter() - start, 2)
            report["checks"].append({"name": name, "seconds": elapsed})
            print(f"PASS {name} ({elapsed}s)", flush=True)
            return result

        try:
            client = wsgi.server.test_client()
            def http_check():
                for endpoint in ("/", "/healthz", "/_dash-layout", "/_dash-dependencies"):
                    assert client.get(endpoint).status_code == 200
                for tab in ("dashboard", "data-analysis", "pv-forecasting", "cooling-demand"):
                    response = client.post("/_dash-update-component", json={
                        "output": "page-content.children", "outputs": {"id": "page-content", "property": "children"},
                        "changedPropIds": ["app-tabs.value"], "state": [],
                        "inputs": [{"id": "app-tabs", "property": "value", "value": tab},
                                   {"id": "system-select", "property": "value", "value": 6}],
                    })
                    assert response.status_code == 200, response.get_data(as_text=True)
            check("HTTP and four tabs", http_check)
            paths, pipeline = check("PV preprocessing and export", lambda: export_preprocessing_artifacts(list_system_dataset_paths()[0].name, {}))
            metadata = json.loads(Path(paths["json_path"]).read_text(encoding="utf-8"))
            report["pv_rows"] = len(pipeline.dataframe)
            for model in args.models.split(","):
                model = model.strip()
                info = check(f"PV {model} training", lambda: pv.train_model({
                    "artifact_id": metadata["artifact_id"], "horizons": [5, 15, 30], "models": [model],
                    "model_settings": {model: {"n_estimators": 30, "iterations": 30, "epochs": 1,
                                              "max_training_rows": 2000}},
                }))
                frame = pv._load_artifact_frame(pv.get_artifact(metadata["artifact_id"]))
                timestamp = frame.iloc[-60]["_ts"].isoformat()
                result = check(f"PV {model} forecast curve", lambda: pv.predict_trained_model_range(info["model_token"], {
                    "start": timestamp, "end": (pd.Timestamp(timestamp) + pd.Timedelta(hours=1)).isoformat(),
                }))
                assert result["results"][model]["records"]
                check(f"PV {model} model download", lambda: pv.serialize_trained_model(info["model_token"]))
                def restore():
                    code = f"import wsgi; from services.forecasting_service import predict_trained_model; predict_trained_model({info['model_token']!r}, {{'timestamp': {timestamp!r}}})"
                    subprocess.run([sys.executable, "-c", code], cwd=root, check=True, capture_output=True, text=True)
                check(f"PV {model} restore in fresh process", restore)
                source = cooling.list_cooling_sources()[0]
                df = cooling._load_m3_module().load_dataset(source.path)
                report["cooling_rows"] = len(df)
                result = check(f"Cooling {model} backtest", lambda: cooling.run_cooling_backtest({
                    "source_id": source.source_id, "source_type": "system", "system_id": 6,
                    "profile_id": "lahore_dc_01", "horizons": [10, 20, 30], "models": [model],
                    "start": str(df.iloc[-576]["_ts"]), "end": str(df.iloc[-1]["_ts"]),
                    "model_settings": {model: {"n_estimators": 30, "iterations": 30, "epochs": 1,
                                              "max_training_rows": 2000}},
                    "steady_state_only": False, "auto_calibrate": False,
                }))
                assert result.get("results", {}).get(model, result)["records"] and result["metrics"]
                check(f"Cooling {model} downloads", lambda: cooling.export_cooling_result(result))
            report["status"] = "passed"
        finally:
            stopped.set()
            if sampler:
                sampler.join()
            report["peak_rss_mb"] = round(peak[0] / 1024**2, 1) if peak[0] is not None else None
            report["settings"] = {"model_threads": 2, "training_rows_limit": 2000, "lstm_epochs": 1}
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
            print(f"Report: {args.report.resolve()}", flush=True)
    if report.get("status") != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
