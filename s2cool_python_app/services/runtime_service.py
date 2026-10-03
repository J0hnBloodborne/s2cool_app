"""Shared paths and limits for local runs and the single-process demo server."""

from __future__ import annotations

import os
import shutil
import sys
import threading
import uuid
from datetime import datetime
from functools import wraps
from pathlib import Path

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    APP_ROOT = REPO_ROOT = Path(sys._MEIPASS)
else:
    APP_ROOT = Path(__file__).resolve().parents[1]
    REPO_ROOT = APP_ROOT.parent

DATA_ROOT = Path(os.environ.get("S2COOL_DATA_DIR", REPO_ROOT / "runtime")).resolve()
MODEL_THREADS = max(1, int(os.environ.get("S2COOL_MODEL_THREADS", "2")))
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MODEL_RUN_LOCK = threading.Lock()
PROFILE_LOCK = threading.Lock()


def initialize_runtime() -> None:
    """Seed writable data once; app updates must not replace saved work."""
    seeds = [
        (APP_ROOT / "config", DATA_ROOT / "config", "*.json"),
        (REPO_ROOT / "M2_PVnowcasting_module" / "data",
         DATA_ROOT / "M2_PVnowcasting_module" / "data", "*.csv"),
        (REPO_ROOT / "M3_CoolingLoad_prediction_module" / "data",
         DATA_ROOT / "M3_CoolingLoad_prediction_module" / "data", "*.csv"),
    ]
    for source, destination, pattern in seeds:
        destination.mkdir(parents=True, exist_ok=True)
        for path in source.glob(pattern):
            target = destination / path.name
            if not target.exists():
                shutil.copy2(path, target)


def safe_child(directory: Path, name: str) -> Path:
    """Reject browser-provided paths; accept one plain filename only."""
    if not isinstance(name, str) or not name or "/" in name or "\\" in name:
        raise ValueError("Select a valid dataset filename.")
    path = (directory / name).resolve()
    if path.parent != directory.resolve():
        raise ValueError("Select a valid dataset filename.")
    return path


def run_stamp() -> str:
    return f"{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:12]}"


def serialized_run(error_class):
    """Reject a second heavy run without blocking normal page requests."""
    def decorate(function):
        @wraps(function)
        def run(*args, **kwargs):
            if not MODEL_RUN_LOCK.acquire(blocking=False):
                raise error_class("Another model run is in progress. Try again when it finishes.")
            try:
                return function(*args, **kwargs)
            finally:
                MODEL_RUN_LOCK.release()
        return run
    return decorate


initialize_runtime()
