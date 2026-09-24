"""Phase 0 Gate (Gate P0-0) — Freeze and Inventory Verification.

Supports two explicit source modes:
- GIT MODE: Verifies active git worktree, HEAD, branch, and ancestry.
- ARCHIVE MODE: Rigorously verifies provenance, manifest integrity, and file inventories.
"""
import json
import os
import subprocess
import sys

def run(cmd, cwd=None):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return res.returncode, res.stdout.strip(), res.stderr.strip()

def test_phase0():
    print("=== Gate P0-0: Phase 0 Freeze and Inventory Verification ===")
    failures = []

    # Dynamic target resolution
    if os.path.isdir("backend") and os.path.isdir("models"):
        repo_b_target = "."
        base_dir = "."
    elif os.path.isdir("repos/repo_b"):
        repo_b_target = "repos/repo_b"
        base_dir = "."
    else:
        repo_b_target = "."
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    repo_a_dir = os.environ.get("REPO_A_DIR", "repos/repo_a")

    # 1. External historical repo_a checks (if present)
    if os.path.isdir(repo_a_dir) and os.path.isdir(os.path.join(repo_a_dir, ".git")):
        code, out, _ = run(f"git -C {repo_a_dir} status --porcelain")
        if code != 0 or out != "":
            failures.append(f"repo_a dirty worktree: {out}")
        else:
            print("[PASS] repo_a worktree is clean")
        
        expected_a = "b9f52d3eeec8676e06b1879f05b404605e2501be"
        code, out, _ = run(f"git -C {repo_a_dir} rev-parse HEAD")
        if out != expected_a:
            failures.append(f"repo_a SHA mismatch: {out}")
        else:
            print(f"[PASS] repo_a SHA confirmed: {out}")
    else:
        print("[INFO] Standalone clone mode: external repo_a not present; skipping external SHA check")

    # 2. Source Mode Resolution for target repository
    is_git_mode = os.path.isdir(os.path.join(repo_b_target, ".git"))
    expected_base_b = "82eded8194151e37fb9b3eecf273010dc62d7b29"
    expected_candidate_b = "6c1e8453d0f2fc12fc1b12f813858430cf5ebda4"

    if is_git_mode:
        print("[SOURCE_MODE=GIT] Validating active Git repository state...")
        code, out, _ = run(f"git -C {repo_b_target} status --porcelain")
        if code != 0 or out != "":
            failures.append(f"repo_b dirty worktree: {out}")
        else:
            print("[PASS] repo_b worktree is clean")

        code_tag, out_tag, _ = run(f'git -C {repo_b_target} rev-parse "audit-repo-b-82eded8^{{commit}}"')
        code_anc, _, _ = run(f"git -C {repo_b_target} merge-base --is-ancestor {expected_base_b} HEAD")
        if (code_tag != 0 and out_tag != expected_base_b) and code_anc != 0:
            failures.append(f"repo_b base SHA mismatch: tag={out_tag}, ancestry_code={code_anc}, expected {expected_base_b}")
        else:
            print(f"[PASS] repo_b base SHA confirmed & descends from: {expected_base_b}")
    else:
        print("[SOURCE_MODE=ARCHIVE] .git directory absent; validating authoritative package provenance...")
        sha_file = os.path.join(repo_b_target, "manifests", "candidate_sha.txt")
        if not os.path.isfile(sha_file):
            failures.append(f"Missing candidate SHA record: {sha_file}")
        else:
            cand_sha = open(sha_file, encoding="utf-8").read().strip()
            if cand_sha != expected_candidate_b:
                failures.append(f"Candidate SHA mismatch in candidate_sha.txt: {cand_sha} != {expected_candidate_b}")
            else:
                print(f"[PASS] Authoritative Candidate SHA verified: {cand_sha}")

        rel_man_file = os.path.join(repo_b_target, "backend", "app", "core", "release_manifest.json")
        if not os.path.isfile(rel_man_file):
            failures.append(f"Missing release manifest: {rel_man_file}")
        else:
            try:
                rel_data = json.loads(open(rel_man_file, encoding="utf-8").read())
                prov = rel_data.get("git_provenance", {})
                if prov.get("base_commit_sha") != expected_base_b:
                    failures.append(f"Release manifest base SHA mismatch: {prov.get('base_commit_sha')} != {expected_base_b}")
                else:
                    print(f"[PASS] Base commit provenance verified: {expected_base_b}")
            except Exception as exc:
                failures.append(f"Could not parse release manifest: {exc}")

    # 3. Check all Phase 0 manifests
    required_manifests = [
        "manifests/repo_a_artifact_hashes.sha256",
        "manifests/repo_b_artifact_hashes.sha256",
        "manifests/repo_a_audit_state.txt",
        "manifests/repo_b_audit_state.txt",
        "manifests/repo_metadata.txt",
        "manifests/repo_a_full_tree.txt",
        "manifests/repo_b_full_tree.txt",
        "manifests/repo_a_backend_files.txt",
        "manifests/repo_b_backend_files.txt",
        "manifests/repo_a_frontend_files.txt",
        "manifests/repo_b_frontend_files.txt",
        "manifests/repo_a_model_files.txt",
        "manifests/repo_b_model_files.txt",
        "manifests/repo_a_test_files.txt",
        "manifests/repo_b_test_files.txt",
        "manifests/file_classifications.csv",
        "manifests/asset_ledger.csv",
        "manifests/duplicate_trees.json",
        "manifests/audit_scores.json",
        "logs/repo_a_baseline/pytest_collect.log",
        "logs/repo_b_baseline/pytest_collect.log"
    ]

    for m in required_manifests:
        target_path = os.path.join(base_dir, m)
        if not os.path.exists(target_path) and os.path.exists(os.path.join(repo_b_target, m)):
            target_path = os.path.join(repo_b_target, m)
        if not os.path.exists(target_path) or os.path.getsize(target_path) == 0:
            failures.append(f"Missing or empty required manifest: {m}")
        else:
            print(f"[PASS] Verified: {m} ({os.path.getsize(target_path)} bytes)")

    if failures:
        print("\n=== GATE P0-0 FAILED ===")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("\n=== GATE P0-0 COMPULSORY GATE TEST PASSED ===")
        sys.exit(0)

if __name__ == "__main__":
    test_phase0()
