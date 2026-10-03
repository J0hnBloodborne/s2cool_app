"""Add only S2Cool's site after checking the running proxy and local app."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", default="s2cool.duckdns.org")
    parser.add_argument("--expected-sha256", required=True, help="Hash recorded during server inspection")
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise SystemExit("Run with sudo.")
    if not re.fullmatch(r"[a-z0-9]+(?:[.-][a-z0-9]+)+", args.domain):
        raise SystemExit("Use a plain domain name.")
    config = Path("/etc/caddy/Caddyfile")
    original = config.read_bytes()
    if hashlib.sha256(original).hexdigest() != args.expected_sha256:
        raise SystemExit("Proxy config changed since inspection. Inspect it again before proceeding.")
    active = json.load(urllib.request.urlopen("http://127.0.0.1:2019/config/", timeout=5))
    saved = json.loads(subprocess.check_output([
        "caddy", "adapt", "--config", str(config), "--adapter", "caddyfile",
    ]))
    if active != saved:
        raise SystemExit("The running proxy differs from its saved file. No changes made.")
    if args.domain.encode() in original:
        raise SystemExit("This domain is already in the proxy config. No changes made.")
    with urllib.request.urlopen("http://127.0.0.1:8050/healthz", timeout=10) as response:
        if json.load(response) != {"status": "ok"}:
            raise SystemExit("The app health check failed. No proxy changes made.")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = config.with_name(f"Caddyfile.before-s2cool-{stamp}")
    candidate = config.with_name("Caddyfile.s2cool-candidate")
    block = f"\n\n{args.domain} {{\n    encode gzip\n    request_body {{\n        max_size 40MB\n    }}\n    reverse_proxy 127.0.0.1:8050 {{\n        transport http {{\n            keepalive 30s\n        }}\n    }}\n}}\n"
    candidate.write_bytes(original + block.encode())
    candidate.chmod(0o644)
    subprocess.run(["caddy", "validate", "--config", str(candidate), "--adapter", "caddyfile"], check=True)
    backup.write_bytes(original)
    backup.chmod(0o600)
    # Save the exact previous active config too, without printing its contents.
    active_backup = backup.with_name(backup.name + ".json")
    active_backup.write_text(json.dumps(active), encoding="utf-8")
    active_backup.chmod(0o600)
    try:
        config.write_bytes(candidate.read_bytes())
        subprocess.run(["systemctl", "reload", "caddy"], check=True)
    except Exception:
        config.write_bytes(original)
        subprocess.run(["systemctl", "reload", "caddy"], check=True)
        raise
    print(f"Added {args.domain}. Original site config preserved. Backup: {backup}")


if __name__ == "__main__":
    main()
