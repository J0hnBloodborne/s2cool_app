"""Start the complete app: python run.py (http://127.0.0.1:8050)."""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Start S2Cool")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8050)
    parser.add_argument("--dev", action="store_true", help="Use the development server")
    args = parser.parse_args()
    os.environ["HOST"] = args.host
    os.environ["PORT"] = str(args.port)
    from wsgi import app, server

    if args.dev:
        app.run(host=args.host, port=args.port, debug=False)
    elif sys.platform == "win32":
        from waitress import serve
        print(f"S2Cool is running at http://{args.host}:{args.port}", flush=True)
        serve(server, host=args.host, port=args.port, threads=4,
              max_request_body_size=40 * 1024 * 1024)
    else:
        root = Path(__file__).resolve().parent
        raise SystemExit(subprocess.call([
            sys.executable, "-m", "gunicorn", "-c",
            str(root / "deployment" / "gunicorn.conf.py"), "wsgi:server",
        ], cwd=root))


if __name__ == "__main__":
    main()
