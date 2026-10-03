# Demo on the existing server

The supplied SSH key reaches an Ubuntu x86 machine with about 1 GB of RAM.
It already runs another app, PostgreSQL, and Caddy. It is not the proposed
Oracle A1 machine.

S2Cool gets its own service, Python environment, login, and data folder.
It listens at `127.0.0.1:8050`. The existing app stays on port 8000.

The small demo limits training to 2,000 rows, 30 trees, and a depth of 6.
LSTMs, CatBoost, LightGBM, and thermal calibration are disabled here.
XGBoost uses the existing sklearn Gradient Boosting fallback; the UI labels
that fallback. Extra Trees and Random Forest are available too.
The saved model details record the settings actually used.

The service can use at most 450 MB of RAM, 256 MB of swap, and 35% of one
CPU core. These limits apply to S2Cool only. If it exceeds its memory limit,
the service can stop; this does not make every possible demo run succeed.
Use the local setup or a larger separate VM for LSTM training.

## Install

Build the usual bundle with `scripts/build_bundle.py`. Upload it and extract
it into `/opt/s2cool/app`. Create `/etc/s2cool/demo.env` with
`scripts/configure_demo_access.py`, then run:

```bash
cd /opt/s2cool/app
sudo bash deployment/install-shared-server.sh
curl --fail http://127.0.0.1:8050/healthz
sudo systemctl status s2cool --no-pager
```

This script installs only the base packages in S2Cool's own environment.
It does not change the existing app, database, or Caddy configuration.
`deployment/requirements-shared.lock.txt` records the tested server package
versions and is used when it is present. It is for this Linux x86 setup.

## Add the domain

Save a copy of the current `/etc/caddy/Caddyfile`. Add this block alongside
the existing site block:

```caddyfile
s2cool.duckdns.org {
    encode gzip
    request_body {
        max_size 40MB
    }
    reverse_proxy 127.0.0.1:8050 {
        transport http {
            keepalive 30s
        }
    }
}
```

Validate the full file before applying it. Reload Caddy without stopping it:

```bash
sudo caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
sudo systemctl reload caddy
```

Check both domain names after the reload. The old site should keep its
original route. The new site should require the S2Cool demo login.
[Caddy reload and validation](https://caddyserver.com/docs/command-line)
The proxy idle timeout is shorter than the app timeout. This avoids reusing
a connection that the app has already closed.
[Caddy connection settings](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy)

Saved work is in `/var/lib/s2cool`. Login settings are in
`/etc/s2cool/demo.env`. Backups use `deployment/backup.sh`.
To remove the demo from service, stop and disable `s2cool`, then remove
only its domain block from Caddy and validate and reload again.
The original Caddy backup provides another way to restore the proxy config.

## Live browser check

From the local setup, use a private JSON file with `username` and `password`:

```powershell
.\.venv\Scripts\python.exe scripts\browser_smoke.py --url https://s2cool.duckdns.org --auth-file .env.demo-access.json --timeout 180000
```

Keep the login file out of Git. This checks generation, exports, training,
prediction, and downloads against the running app. It does not launch
another model process on the server.

The current PC's network presents a Fortinet certificate instead of the
server certificate. If that causes a certificate warning, use the SSH
tunnel from the Oracle guide with local port 8052, or run the browser check
through an SSH SOCKS proxy:

```powershell
ssh -i "C:\path\server.key" -N -D 127.0.0.1:1080 ubuntu@s2cool.duckdns.org
.\.venv\Scripts\python.exe scripts\browser_smoke.py --url https://s2cool.duckdns.org --auth-file .env.demo-access.json --proxy socks5://127.0.0.1:1080 --timeout 180000 --report-dir build/live-browser
```

This keeps certificate checks enabled and reaches the server through SSH.
