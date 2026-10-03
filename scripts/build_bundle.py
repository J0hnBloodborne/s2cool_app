"""Create one deployment bundle without local environments, secrets, or outputs."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
TREES = ("s2cool_python_app", "M2_PVnowcasting_module", "M3_CoolingLoad_prediction_module",
         "deployment", "scripts", "tests")
FILES = ("run.py", "wsgi.py", "requirements.txt", "requirements-models.txt", "requirements-lstm.txt",
         "requirements-dev.txt", "README.md", "README_ORACLE.md", "DEPLOYMENT_FILE_MANIFEST.md",
         "setup-local.ps1", "pytest.ini", "ruff.toml", ".env.example", ".gitattributes", "DEPLOYMENT_STATUS.md",
         "README_SHARED_SERVER.md")


def main():
    destination = ROOT / "build" / "s2cool-oracle-demo.zip"
    destination.parent.mkdir(parents=True, exist_ok=True)
    paths = [ROOT / name for name in FILES]
    for tree in TREES:
        paths.extend(path for path in (ROOT / tree).rglob("*") if path.is_file()
                     and not any(part in {"__pycache__", "forecast", "preprocessing", "catboost_info"}
                                 for part in path.relative_to(ROOT).parts)
                     and path.suffix not in {".pyc", ".joblib", ".pkl", ".log"})
    with ZipFile(destination, "w", compression=ZIP_DEFLATED) as bundle:
        for path in sorted(set(paths)):
            bundle.write(path, path.relative_to(ROOT).as_posix())
    print(f"{destination} ({destination.stat().st_size / 1024**2:.1f} MB)")


if __name__ == "__main__":
    main()
