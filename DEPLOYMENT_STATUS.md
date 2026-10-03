# Demo readiness — 3 October 2026

The app runs locally at `http://127.0.0.1:8050`. The Oracle A1 deployment
bundle and install steps are ready. The app has not been installed on the
Oracle VM yet; its connection details have not been provided.

## Fixed

- The settings loader now finds the bundled settings.
- The app starts on System 06, which has sample data.
- Saved-model uploads are rejected by the server. The upload control is removed.
- CSV uploads use a new server-made filename and a 20 MB limit.
- Model downloads use the browser.
- Trained PV models can be restored after a restart, including LSTMs.
- Data, profiles, models, and exports have one writable data folder.
- Export names are unique. Existing saved profiles survive app updates.
- Only one model run can start at a time. Normal page requests can continue.
- The Oracle service requires a demo login and starts again after a crash.
- The dashboard no longer displays a made-up live status or update time.

M2 and M3 remain in their code folders. One start command loads both.
The deployment bundle includes both modules and the dashboard.

## Checked locally

35 automated checks passed. These cover all four working tabs, upload
rejection, file paths, login, all six model choices for PV and cooling,
model downloads, restart, and backup restore. Ruff and package checks passed.

A Chrome check completed dataset generation and export, PV training,
model download, prediction, a cooling backtest, and CSV downloads. It found
no browser errors or server errors.

A full-data check used 67,856 raw PV rows and 57,888 cooling rows. PV
preprocessing retained 35,601 rows. Extra Trees and LSTM runs passed for
both modules. This check used up to 2,000 training rows, one LSTM epoch,
three horizons, and two model threads. Peak memory in the main check process
was about 928 MB on this Windows x86 PC. These are execution checks, not
accuracy results or A1 performance estimates.

A live Open-Meteo check returned 24 hourly weather rows. ARM64 package
resolution succeeded for Python 3.12, including CPU-only PyTorch. This
checks package availability; the actual A1 VM must still run the model check.

## Finish on Oracle

1. Create or connect to the Ubuntu A1 VM.
2. Upload `build/s2cool-oracle-demo.zip`.
3. Run the install script and set the demo login.
4. Run the full-data check on the VM.
5. Open the app through the SSH tunnel and try the demo flow.
6. Save an off-server backup of work that must be kept.

Use [README_ORACLE.md](README_ORACLE.md) for the commands. The older paid
hosting review describes the earlier launch plan. This demo now targets
the Oracle A1 free tier, as agreed.
