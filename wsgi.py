"""One entry point for all three app folders, independent of working directory."""

import os
import sys
from pathlib import Path

_threads = os.environ.get("S2COOL_MODEL_THREADS", "2")
for _variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_variable, _threads)
os.environ.setdefault("MPLBACKEND", "Agg")
sys.path.insert(0, str(Path(__file__).resolve().parent / "s2cool_python_app"))

from app import app, server  # noqa: E402, F401
