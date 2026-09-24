"""Gate P0-2: Base Selection and Branch Controls Verification.

Supports two explicit source modes:
- GIT MODE: Verifies active branch (main or integration/sih-round2-selective-merge).
- ARCHIVE MODE: Validates integration branch declaration in release manifest, plus single trees.
"""
import json
import os
import subprocess
import sys

if os.path.isdir("backend") and os.path.isdir("models"):
    REPO_B = os.path.abspath(".")
elif os.path.isdir("repos/repo_b"):
    REPO_B = os.path.abspath("repos/repo_b")
else:
    REPO_B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run(cmd, cwd=None):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return res.returncode, res.stdout.strip(), res.stderr.strip()

def test_phase2():
    print("=== Gate P0-2: Base Selection and Branch Controls Verification ===")
    failures = []

    # 1. Integration branch validation
    is_git_mode = os.path.isdir(os.path.join(REPO_B, ".git"))
    if is_git_mode:
        print("[SOURCE_MODE=GIT] Checking active Git branch...")
        code, branch, _ = run("git branch --show-current", cwd=REPO_B)
        if branch not in ["integration/sih-round2-selective-merge", "main"]:
            failures.append(f"repo_b branch is '{branch}', expected 'integration/sih-round2-selective-merge' or 'main'")
        else:
            print(f"[PASS] repo_b integration/main branch confirmed: {branch}")
    else:
        print("[SOURCE_MODE=ARCHIVE] .git directory absent; validating integration branch via release manifest...")
        rel_man_file = os.path.join(REPO_B, "backend", "app", "core", "release_manifest.json")
        if not os.path.isfile(rel_man_file):
            failures.append(f"Missing release manifest: {rel_man_file}")
        else:
            try:
                rel_data = json.loads(open(rel_man_file, encoding="utf-8").read())
                prov = rel_data.get("git_provenance", {})
                branch = prov.get("integration_branch")
                if branch not in ["integration/sih-round2-selective-merge", "main"]:
                    failures.append(f"Invalid integration branch in release manifest: '{branch}'")
                else:
                    print(f"[PASS] Authoritative integration branch confirmed: {branch}")
            except Exception as exc:
                failures.append(f"Failed to parse release manifest: {exc}")

    # 2. Check canonical single backend/app and frontend/src
    backend_app = os.path.join(REPO_B, "backend", "app")
    if not os.path.isdir(backend_app):
        failures.append(f"Missing backend/app at: {backend_app}")
    else:
        print(f"[PASS] Singular backend directory confirmed: {backend_app}")

    frontend_src = os.path.join(REPO_B, "frontend", "src")
    if not os.path.isdir(frontend_src):
        failures.append(f"Missing frontend/src at: {frontend_src}")
    else:
        print(f"[PASS] Singular frontend directory confirmed: {frontend_src}")

    # 3. Check NO duplicate trees in repo_b
    forbidden_trees = ["Builder-2", "Parinidhi", "Frontend-Original", "Overview"]
    for tree in forbidden_trees:
        p = os.path.join(REPO_B, tree)
        if os.path.exists(p):
            failures.append(f"Forbidden duplicate tree found in repo_b: {p}")
        else:
            print(f"[PASS] Clean from duplicate tree: {tree}")

    # 4. Check single model registry
    models_v3 = os.path.join(REPO_B, "models", "v3")
    if not os.path.isdir(models_v3):
        failures.append(f"Missing models/v3 directory in repo_b: {models_v3}")
    else:
        v3_files = sorted(os.listdir(models_v3))
        print(f"[PASS] models/v3 confirmed with {len(v3_files)} items: {v3_files}")

    # 5. Check manifest governance docs
    for mf in [
        "manifests/canonical_directory_map.md",
        "manifests/import_allowlist.csv",
        "manifests/import_denylist.csv",
        "manifests/code_owners.md"
    ]:
        target_mf = os.path.join(REPO_B, mf) if not os.path.exists(mf) else mf
        if not os.path.exists(target_mf) or os.path.getsize(target_mf) == 0:
            failures.append(f"Missing governance manifest: {mf}")
        else:
            print(f"[PASS] Governance manifest verified: {mf}")

    if failures:
        print("\n=== GATE P0-2 FAILED ===")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("\n=== GATE P0-2 COMPULSORY GATE TEST PASSED ===")
        sys.exit(0)

if __name__ == "__main__":
    test_phase2()
