#!/usr/bin/env bash
set -euo pipefail

[[ ${EUID} -eq 0 ]] || { echo "Run with sudo." >&2; exit 1; }
app_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ "$app_dir" == /opt/s2cool/app ]] || { echo "Put the app in /opt/s2cool/app first." >&2; exit 1; }
[[ -f /etc/s2cool/demo.env ]] || { echo "Create /etc/s2cool/demo.env with the demo login first." >&2; exit 1; }
if ss -H -ltn 'sport = :8050' | grep -q . && ! systemctl is-active --quiet s2cool; then
    echo "Port 8050 is already in use. No changes made." >&2
    exit 1
fi
id s2cool >/dev/null 2>&1 || useradd --system --home /var/lib/s2cool --shell /usr/sbin/nologin s2cool
install -d -o s2cool -g s2cool -m 700 /var/lib/s2cool
python3 -m venv "$app_dir/.venv"
requirements="$app_dir/deployment/requirements-shared.lock.txt"
[[ -f "$requirements" ]] || requirements="$app_dir/requirements.txt"
# Build only this app's environment, within a temporary resource-limited unit.
# No system packages, existing services, database, or proxy config are changed.
systemd-run --unit=s2cool-install --collect --wait --pipe \
    -p MemoryMax=400M -p MemorySwapMax=256M -p CPUQuota=35% -p Nice=15 \
    "$app_dir/.venv/bin/python" -m pip install --no-cache-dir --only-binary=:all: \
    -r "$requirements"
install -m 644 "$app_dir/deployment/s2cool.service" /etc/systemd/system/s2cool.service
install -d -m 755 /etc/systemd/system/s2cool.service.d
install -m 644 "$app_dir/deployment/shared-server.conf" /etc/systemd/system/s2cool.service.d/limits.conf
systemctl daemon-reload
systemctl enable s2cool.service
systemctl restart s2cool.service
for attempt in {1..60}; do
    if curl --fail --silent http://127.0.0.1:8050/healthz >/dev/null; then
        echo "Small demo is running on localhost:8050. The existing proxy is unchanged."
        exit 0
    fi
    sleep 1
done
journalctl -u s2cool.service -n 30 --no-pager
exit 1
