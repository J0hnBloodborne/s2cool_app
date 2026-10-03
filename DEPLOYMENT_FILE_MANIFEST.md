# Deployment file manifest

The Oracle demo now uses `scripts/build_bundle.py` and `README_ORACLE.md`.
The bundle includes all three code folders and one root entry point.
Writable work lives outside those folders in `S2COOL_DATA_DIR`.

The list below is the original Render file list.

The GitHub deployment repository should contain these runtime trees:

- `s2cool_python_app/`
  - `app.py`, `requirements.txt`
  - `pages/`, `services/`, `components/`, `models/`, `config/`, `assets/`
- `M2_PVnowcasting_module/`
  - `pv_hybrid_forecasting_multihorizon.py`
  - `data/` containing only the selected PV weather CSV files
- `M3_CoolingLoad_prediction_module/`
  - `cooling_hybrid_forecasting_multihorizon.py`
  - `data/` containing only the selected cooling measurement CSV files
- `render.yaml`
- `.gitignore`

Exclude virtual environments, caches, notebooks, debug scripts, generated forecast/preprocessing output, unrelated research folders, and local secrets.

Render settings are defined in `render.yaml`. The service runs from `s2cool_python_app` so its existing imports continue to work, while the repository root remains available to the M2/M3 path resolution.
