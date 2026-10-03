# Demo readiness — 4 October 2026

The app runs locally at `http://127.0.0.1:8050` and is deployed at
`https://s2cool.duckdns.org` with a demo login. The supplied SSH key reaches
the existing Ubuntu x86 server with about 1 GB of RAM. It does not reach an
A1 machine. The separate A1 setup remains ready for a larger demo.

The existing app and PostgreSQL are still running.
S2Cool has its own service and writable data folder. Its service is limited
to 450 MB of RAM, 256 MB of swap, and 35% of one CPU core.
Training settings are capped at 2,000 rows, 30 trees, and a depth of 6.
LSTMs and thermal calibration stay off this small server.

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

39 automated checks passed. These cover all four working tabs, upload
rejection, file paths, login, all six model choices for PV and cooling,
model downloads, restart, backup restore, and enforced small-demo limits.
Ruff and package checks passed.

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

## Checked on the live server

The Chrome demo flow passed at `https://s2cool.duckdns.org`: dataset
generation and export, PV training, model download, prediction, cooling
backtest, and CSV downloads. It reported no browser or server errors.
The server model files record the enforced small-demo training limits.

The whole S2Cool service peaked at about 351 MB during that check. It had
no automatic restarts or memory kills. This was a short demo check, not a
long load test. The existing site kept returning HTTP 200. The existing app,
Caddy, and PostgreSQL kept their original process IDs. The existing app's
service file and the original proxy site block are unchanged.

The first live check exposed a proxy connection timeout mismatch. The
S2Cool proxy and app settings now keep the proxy timeout shorter. The demo
login also recognises an already-verified credential without hashing it
again for each request. Incorrect passwords are still rejected.

The original proxy file is saved at
`/etc/caddy/Caddyfile.before-s2cool-20261003T210204Z`. S2Cool data was backed
up under `/var/backups/s2cool` after the live check. The current PC's network
presents an untrusted Fortinet certificate; the browser check used an SSH
proxy to verify the real server certificate with certificate checks enabled.

## Separate Oracle A1 option

1. Create or connect to the Ubuntu A1 VM.
2. Upload `build/s2cool-oracle-demo.zip`.
3. Run the install script and set the demo login.
4. Run the full-data check on the VM.
5. Open the app through the SSH tunnel and try the demo flow.
6. Save an off-server backup of work that must be kept.

Use [README_ORACLE.md](README_ORACLE.md) for that larger server.
Use [README_SHARED_SERVER.md](README_SHARED_SERVER.md) for the current
shared server, its limits, checks, and rollback steps. The older hosting
review describes the earlier launch plan.
