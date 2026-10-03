#!/usr/bin/env bash
set -euo pipefail
[[ ${EUID} -eq 0 ]] || { echo "Run with sudo." >&2; exit 1; }
install -d -m 700 /var/backups/s2cool
archive="/var/backups/s2cool/data-$(date -u +%Y%m%dT%H%M%SZ).tar.gz"
systemctl stop s2cool.service
trap 'systemctl start s2cool.service' EXIT
tar -czf "$archive" --exclude='*.tmp' --exclude='.tmp_uploads' -C /var/lib/s2cool .
chmod 600 "$archive"
echo "$archive"
