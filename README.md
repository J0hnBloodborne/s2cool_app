# S2Cool demo

Run the whole app from this folder. M2 handles solar power. M3 handles cooling
demand. The dashboard uses both. They ship and run together.

## Start on this Windows PC

The environment is already installed here. Run:

```powershell
.\.venv\Scripts\python.exe run.py
```

Open <http://127.0.0.1:8050>. To set up another Windows PC, run
`powershell -ExecutionPolicy Bypass -File setup-local.ps1` first.
Use Python 3.11 or 3.12.

## Try the demo

1. Open **Data Analysis**. Click **Analyze Existing System**. System 06 has data.
2. Open **Dataset Builder** and click **Generate Dataset**.
3. Click **Export Dataset for Analysis** at the bottom of the page.
4. Open **PV Forecasting**. Select the exported data. Train a model, then
   predict a time or generate a curve within the source dates.
5. Open **Cooling Demand**. Keep System 06 and the provided cooling profile.
   Run a backtest or generate the latest forecast.

Start with XGBoost or Extra Trees. For a quick LSTM demonstration, set its
epochs to 1. Higher settings take more time.

You can download data, results, and trained PV models through the browser.
Choose **Saved models on this server** to reuse a model from an earlier run.
Saved-model uploads are disabled because those files can run code.

## Where work is saved

New data, profiles, exports, and trained PV models go into `runtime/`.
Set `S2COOL_DATA_DIR` to use another folder. The Oracle setup uses
`/var/lib/s2cool`, so an app update keeps saved work.

The three code folders remain together. Moving them into one folder would
add work without changing how the demo runs. `run.py` and `wsgi.py` give the
app one starting point. All paths are based on the installed files rather
than the terminal's current folder.

## Oracle A1

Follow [README_ORACLE.md](README_ORACLE.md). It includes the upload, install,
login, restart, and backup steps. The server uses one app process and allows
one model run at a time. Pages can still load during training.

For the existing 1 GB x86 server, use [README_SHARED_SERVER.md](README_SHARED_SERVER.md)
and its smaller demo limits instead.

## Checks

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe scripts\smoke_demo.py --full
```

The full-data check uses the bundled data, three forecast horizons,
up to 2,000 training rows, and one LSTM epoch. It checks execution,
downloads, and model restore. It does not establish forecast accuracy or
predict the speed of the Oracle server.

The dashboard, data analysis, PV forecasting, and cooling demand tabs work.
The other tabs are planned. This is a shared demo workspace. Cooling runs
use synthetic measurements by default; choose experimental mode and upload
matching measurements when a measured comparison is needed. PV forecasts
use the selected historical data, including its calendar lookup. They do
not fetch live future weather.
