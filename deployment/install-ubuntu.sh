#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
    echo "Run: sudo bash deployment/install-ubuntu.sh" >&2
    exit 1
fi
app_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "$app_dir" != /opt/s2cool/app ]]; then
    echo "Unzip the deployment bundle into /opt/s2cool/app first." >&2
    exit 1
fi
if [[ "$(uname -m)" != aarch64 ]]; then
    echo "This install script targets Oracle A1 (aarch64)." >&2
    exit 1
fi
apt-get update
apt-get install -y python3 python3-venv libgomp1 curl
id s2cool >/dev/null 2>&1 || useradd --system --home /var/lib/s2cool --shell /usr/sbin/nologin s2cool
install -d -o s2cool -g s2cool -m 700 /var/lib/s2cool
install -d -m 700 /etc/s2cool
python3 -m venv "$app_dir/.venv"
"$app_dir/.venv/bin/python" -m pip install --upgrade pip
"$app_dir/.venv/bin/python" -m pip install -r "$app_dir/requirements.txt" -r "$app_dir/requirements-models.txt"
"$app_dir/.venv/bin/python" -m pip install -r "$app_dir/requirements-lstm.txt"
if [[ ! -f /etc/s2cool/demo.env ]]; then
    "$app_dir/.venv/bin/python" "$app_dir/scripts/configure_demo_access.py" /etc/s2cool/demo.env
fi
install -m 644 "$app_dir/deployment/s2cool.service" /etc/systemd/system/s2cool.service
systemctl daemon-reload
systemctl enable s2cool.service
systemctl restart s2cool.service
for attempt in {1..60}; do
    if curl --fail --silent http://127.0.0.1:8050/healthz >/dev/null; then
        echo "S2Cool is running. Use the SSH tunnel shown in README_ORACLE.md."
        exit 0
    fi
    sleep 1
done
journalctl -u s2cool.service -n 30 --no-pager
exit 1
