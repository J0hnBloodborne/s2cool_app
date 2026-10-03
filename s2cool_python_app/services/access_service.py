"""Optional shared demo login; required by the Oracle service configuration."""

import hmac
import os
import secrets
import threading

from flask import Response, request
from werkzeug.security import check_password_hash


def configure_access(server) -> None:
    username = os.environ.get("S2COOL_AUTH_USER", "")
    password_hash = os.environ.get("S2COOL_PASSWORD_HASH", "")
    required = os.environ.get("S2COOL_REQUIRE_AUTH", "0") == "1"
    if (required or username or password_hash) and not (username and password_hash):
        raise RuntimeError("Set both S2COOL_AUTH_USER and S2COOL_PASSWORD_HASH to enable demo access.")
    server.config["MAX_CONTENT_LENGTH"] = 40 * 1024 * 1024
    verified_fingerprint = None
    fingerprint_key = secrets.token_bytes(32)
    fingerprint_lock = threading.Lock()

    def valid_password(password):
        nonlocal verified_fingerprint
        fingerprint = hmac.digest(fingerprint_key, password.encode("utf-8"), "sha256")
        with fingerprint_lock:
            if verified_fingerprint is not None and hmac.compare_digest(fingerprint, verified_fingerprint):
                return True
        if not check_password_hash(password_hash, password):
            return False
        # One already-verified credential can be recognised without repeating
        # the expensive password hash on every asset and callback. No plaintext
        # password is cached; changing the service login requires a restart.
        with fingerprint_lock:
            verified_fingerprint = fingerprint
        return True

    @server.before_request
    def require_demo_login():
        if request.path == "/healthz" or not username:
            return None
        auth = request.authorization
        if (auth and auth.type == "basic" and
                hmac.compare_digest((auth.username or "").encode("utf-8"), username.encode("utf-8")) and
                valid_password(auth.password or "")):
            return None
        return Response("Demo login required.", status=401,
                        headers={"WWW-Authenticate": 'Basic realm="S2Cool demo"'})

    @server.after_request
    def response_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        if request.path.startswith("/_dash"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @server.get("/healthz")
    def health():
        return {"status": "ok"}
