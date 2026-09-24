"""Verification script for Veyra ML artifacts, Git-LFS detection, release manifest authority, and cryptographic provenance."""
import hashlib
import json
import sys
from pathlib import Path

GIT_LFS_HEADER_PREFIX = b"version https://git-lfs.github.com/spec/v1"

def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()

def is_git_lfs_pointer(path: Path) -> bool:
    if not path.is_file():
        return False
    if path.stat().st_size > 1024:
        return False
    try:
        content = path.read_bytes()
        return content.startswith(GIT_LFS_HEADER_PREFIX)
    except Exception:
        return False

def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    artifact_manifest_path = repo_root / "models" / "v3" / "artifact_manifest.json"
    release_manifest_path = repo_root / "backend" / "app" / "core" / "release_manifest.json"
    
    print("=" * 65)
    print("Veyra ML Artifact Chain & SHA-256 Provenance Verification")
    print("=" * 65)
    
    if not artifact_manifest_path.is_file():
        print(f"[FAIL] Artifact manifest file missing: {artifact_manifest_path}")
        return 1
    
    try:
        manifest = json.loads(artifact_manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[FAIL] Could not parse artifact manifest JSON: {exc}")
        return 1
    
    artifacts = manifest.get("artifacts", {})
    all_passed = True
    
    # 1. Verify individual artifacts from artifact_manifest.json
    for key, spec in artifacts.items():
        rel_path = spec["path"]
        expected_sha = spec["sha256"]
        file_path = repo_root / rel_path
        
        print(f"\nVerifying artifact [{key}]: {rel_path}...")
        
        if not file_path.is_file():
            print(f"  [FAIL] File does not exist: {file_path}")
            all_passed = False
            continue
        
        if is_git_lfs_pointer(file_path):
            print(f"  [FAIL] Detected Git-LFS pointer stub instead of binary weights!")
            print(f"         File size: {file_path.stat().st_size} bytes.")
            print(f"         Action required: Run 'git lfs pull' to fetch actual weights.")
            all_passed = False
            continue
        
        actual_sha = compute_sha256(file_path)
        actual_size = file_path.stat().st_size
        
        if actual_sha != expected_sha:
            print(f"  [FAIL] SHA-256 checksum mismatch!")
            print(f"         Expected: {expected_sha}")
            print(f"         Actual:   {actual_sha}")
            all_passed = False
            continue
        
        print(f"  [PASS] SHA-256 matched: {actual_sha}")
        print(f"  [PASS] File size: {actual_size:,} bytes")
        
        if key == "features":
            try:
                features = json.loads(file_path.read_text(encoding="utf-8"))
                if len(features) != spec.get("feature_count", 50):
                    print(f"  [FAIL] Feature count mismatch: {len(features)} != {spec.get('feature_count', 50)}")
                    all_passed = False
                else:
                    print(f"  [PASS] Feature count verified: {len(features)} canonical features.")
            except Exception as exc:
                print(f"  [FAIL] Could not parse feature schema: {exc}")
                all_passed = False

    # 2. Cross-verify against Release Manifest Authority
    print("\n[Authority] Cross-verifying against backend/app/core/release_manifest.json...")
    if not release_manifest_path.is_file():
        print(f"  [FAIL] Release manifest missing: {release_manifest_path}")
        all_passed = False
    else:
        try:
            rel_manifest = json.loads(release_manifest_path.read_text(encoding="utf-8"))
            
            # Model check
            m_spec = rel_manifest.get("model_artifact", {})
            m_path = repo_root / m_spec.get("path", "")
            if not m_path.is_file() or compute_sha256(m_path) != m_spec.get("sha256"):
                print(f"  [FAIL] Release manifest model SHA mismatch!")
                all_passed = False
            else:
                print(f"  [PASS] Release manifest model SHA verified ({m_spec.get('version')})")

            # Calibrator check
            c_spec = rel_manifest.get("calibrator_artifact", {})
            c_path = repo_root / c_spec.get("path", "")
            if not c_path.is_file() or compute_sha256(c_path) != c_spec.get("sha256"):
                print(f"  [FAIL] Release manifest calibrator SHA mismatch!")
                all_passed = False
            else:
                print(f"  [PASS] Release manifest calibrator SHA verified ({c_spec.get('type')})")

            # Feature schema check
            f_spec = rel_manifest.get("feature_contract", {})
            f_path = repo_root / f_spec.get("feature_names_reference", "")
            if not f_path.is_file() or compute_sha256(f_path) != f_spec.get("sha256"):
                print(f"  [FAIL] Release manifest feature contract SHA mismatch!")
                all_passed = False
            elif f_spec.get("feature_count") != 50:
                print(f"  [FAIL] Release manifest feature count is not 50!")
                all_passed = False
            else:
                print(f"  [PASS] Release manifest 50-feature contract verified")

            # Threshold and routing check
            threshold = m_spec.get("decision_threshold")
            if threshold != 0.06:
                print(f"  [FAIL] Release manifest operational threshold is {threshold}, expected 0.060")
                all_passed = False
            else:
                print(f"  [PASS] Release manifest operational threshold verified: {threshold}")
                
            route = rel_manifest.get("route_authority")
            fallback = rel_manifest.get("fallback_policy")
            if route != "/v1/predict" or fallback != "safe_abstention":
                print(f"  [FAIL] Invalid route or fallback: route={route}, fallback={fallback}")
                all_passed = False
            else:
                print(f"  [PASS] Release authority route: {route}, fallback: {fallback}")

        except Exception as exc:
            print(f"  [FAIL] Error validating release manifest: {exc}")
            all_passed = False

    # 3. Model and Calibrator deserialization + Booster feature-order parity check
    print("\n[Sanity] Verifying model and calibrator loadability with joblib...")
    try:
        import joblib
        import lightgbm as lgb
        from sklearn.isotonic import IsotonicRegression
        
        model_path = repo_root / artifacts["model"]["path"]
        calibrator_path = repo_root / artifacts["calibrator"]["path"]
        features_path = repo_root / artifacts["features"]["path"]
        
        model = joblib.load(model_path)
        print(f"  [PASS] Model loaded: {type(model).__name__}")
        
        # Extract internal Booster
        if hasattr(model, "booster_"):
            booster = model.booster_
        elif isinstance(model, lgb.Booster):
            booster = model
        else:
            booster = getattr(model, "_Booster", model)
            
        if booster.num_feature() != 50:
            print(f"  [FAIL] Booster feature count: {booster.num_feature()} != 50")
            all_passed = False
        else:
            print(f"  [PASS] Booster num_feature verified: {booster.num_feature()}")
            
        features = json.loads(features_path.read_text(encoding="utf-8"))
        if booster.feature_name() != features:
            print(f"  [FAIL] Booster internal feature names do not match feature_names.json!")
            all_passed = False
        else:
            print(f"  [PASS] Booster feature names match feature_names.json in exact order.")
        
        calibrator = joblib.load(calibrator_path)
        if not isinstance(calibrator, IsotonicRegression):
            print(f"  [FAIL] Calibrator is not an IsotonicRegression object: {type(calibrator)}")
            all_passed = False
        else:
            print(f"  [PASS] Calibrator loaded and verified: {type(calibrator).__name__}")
            
    except Exception as exc:
        print(f"  [FAIL] Deserialization verification failed: {exc}")
        all_passed = False

    print("\n" + "=" * 65)
    if all_passed:
        print("All ML artifact integrity and release authority checks PASSED.")
        print("=" * 65)
        return 0
    else:
        print("ML artifact verification FAILED. Please review errors above.")
        print("=" * 65)
        return 1

if __name__ == "__main__":
    sys.exit(main())
