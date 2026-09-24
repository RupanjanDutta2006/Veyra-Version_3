"""Verification script for Veyra environment, dependencies, and package structure."""
import sys
import importlib
from pathlib import Path

REQUIRED_PYTHON_MAJOR = 3
REQUIRED_PYTHON_MINOR = 10

REQUIRED_PACKAGES = [
    "fastapi",
    "uvicorn",
    "pydantic",
    "sqlalchemy",
    "sklearn",
    "lightgbm",
    "joblib",
    "pandas",
    "numpy",
    "pyarrow",
    "httpx",
    "pytest",
]

def main() -> int:
    print("=" * 60)
    print("Veyra Environment & Reproducibility Verification")
    print("=" * 60)
    
    # 1. Python version check
    py_version = sys.version_info
    print(f"[1/4] Checking Python version: {py_version.major}.{py_version.minor}.{py_version.micro}...")
    if (py_version.major, py_version.minor) < (REQUIRED_PYTHON_MAJOR, REQUIRED_PYTHON_MINOR):
        print(f"  [FAIL] Python >= {REQUIRED_PYTHON_MAJOR}.{REQUIRED_PYTHON_MINOR} required, found {py_version.major}.{py_version.minor}")
        return 1
    print("  [PASS] Python version meets requirements.")

    # 2. Package import checks
    print("[2/4] Checking core dependencies importability...")
    missing_packages = []
    for pkg in REQUIRED_PACKAGES:
        try:
            mod = importlib.import_module(pkg)
            version = getattr(mod, "__version__", "unknown")
            print(f"  - {pkg}: {version}")
        except ImportError as exc:
            print(f"  [FAIL] Cannot import {pkg}: {exc}")
            missing_packages.append(pkg)
    
    if missing_packages:
        print(f"  [FAIL] Missing required packages: {missing_packages}")
        return 1
    print("  [PASS] All core dependencies imported successfully.")

    # 3. Application entrypoint import
    print("[3/4] Checking backend application entrypoint (backend.app.main:app)...")
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    try:
        from backend.app.main import app
        print(f"  - App title: '{app.title}', version: '{app.version}'")
        print("  [PASS] Application entrypoint loaded successfully.")
    except Exception as exc:
        print(f"  [FAIL] Failed to import backend.app.main:app: {exc}")
        return 1

    # 4. Packaging configuration check
    print("[4/4] Checking packaging configuration (pyproject.toml)...")
    pyproject_file = repo_root / "pyproject.toml"
    if not pyproject_file.is_file():
        print(f"  [FAIL] pyproject.toml not found at {pyproject_file}")
        return 1
    
    content = pyproject_file.read_text(encoding="utf-8")
    if "[tool.setuptools.packages.find]" not in content:
        print("  [FAIL] [tool.setuptools.packages.find] missing in pyproject.toml")
        return 1
    if 'sqlalchemy>=2.0.0' not in content:
        print("  [FAIL] sqlalchemy>=2.0.0 missing in pyproject.toml dependencies")
        return 1
    print("  [PASS] pyproject.toml contains required setuptools package configuration.")

    print("=" * 60)
    print("All environment and packaging verification checks PASSED.")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
