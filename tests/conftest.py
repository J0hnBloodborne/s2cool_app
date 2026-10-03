import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "s2cool_python_app")]
_runtime = tempfile.TemporaryDirectory(prefix="s2cool-tests-")
os.environ["S2COOL_DATA_DIR"] = _runtime.name
os.environ["S2COOL_MODEL_THREADS"] = "2"
for name in ("S2COOL_AUTH_USER", "S2COOL_PASSWORD_HASH", "S2COOL_REQUIRE_AUTH"):
    os.environ.pop(name, None)

from services.runtime_service import DATA_ROOT, initialize_runtime  # noqa: E402

initialize_runtime()
# Use real bundled rows while keeping repeat tests short. The full-data check
# lives in scripts/smoke_demo.py and runs against a separate temporary folder.
import pandas as pd  # noqa: E402

for path in DATA_ROOT.glob("*/data/*.csv"):
    pd.read_csv(path).head(2880).to_csv(path, index=False)
