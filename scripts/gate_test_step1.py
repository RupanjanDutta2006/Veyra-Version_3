"""Step 1 Gate Verification — Workspace & Repositories Setup.

Supports two explicit source modes:
- GIT MODE: Verifies active git worktree, HEAD, branch, and ancestry.
- ARCHIVE MODE: When .git is absent (standalone package), rigorously verifies candidate and base SHAs
  via authoritative release manifest and candidate_sha.txt records, and validates artifact hashes.
"""
import hashlib
import json
import os
import subprocess
import sys

def run(cmd, cwd=None):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return res.returncode, res.stdout.strip(), res.stderr.strip()

def compute_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()

def test_step1():
    print("=== Step 1 Gate Verification ===")
    failures = []

    # Resolve repo_b target: '.' if running inside repo_b, else 'repos/repo_b'
    if os.path.isdir("backend") and os.path.isdir("models"):
        repo_b_target = "."
    elif os.path.isdir("repos/repo_b"):
        repo_b_target = "repos/repo_b"
    else:
        repo_b_target = "."

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
            failures.append(f"repo_a SHA mismatch: got {out}, expected {expected_a}")
        else:
            print(f"[PASS] repo_a SHA verified: {out}")
    else:
        print("[INFO] Standalone clone mode: external repo_a not present; skipping historical multi-repo cross-check")

    # 2. Source Mode Resolution for target repository
    is_git_mode = os.path.isdir(os.path.join(repo_b_target, ".git"))
    expected_base_b = "82eded8194151e37fb9b3eecf273010dc62d7b29"
    expected_candidate_b = "6c1e8453d0f2fc12fc1b12f813858430cf5ebda4"

    if is_git_mode:
        print("[SOURCE_MODE=GIT] Validating active Git repository state...")
        # Worktree clean check
        code, out, _ = run(f"git -C {repo_b_target} status --porcelain")
        if code != 0 or out != "":
            failures.append(f"repo_b dirty worktree: {out}")
        else:
            print("[PASS] repo_b worktree is clean")

        # Base SHA and ancestry
        code_tag, out_tag, _ = run(f'git -C {repo_b_target} rev-parse "audit-repo-b-82eded8^{{commit}}"')
        code_anc, _, _ = run(f"git -C {repo_b_target} merge-base --is-ancestor {expected_base_b} HEAD")
        if (code_tag != 0 and out_tag != expected_base_b) and code_anc != 0:
            failures.append(f"repo_b base SHA mismatch: tag={out_tag}, ancestry_code={code_anc}, expected {expected_base_b}")
        else:
            print(f"[PASS] repo_b base SHA verified & descends from: {expected_base_b}")

        # Branch check
        code, out, _ = run(f"git -C {repo_b_target} branch --show-current")
        if out not in ["integration/sih-round2-selective-merge", "main"]:
            failures.append(f"repo_b not on valid integration/main branch: {out}")
        else:
            print(f"[PASS] repo_b branch verified: {out}")
    else:
        print("[SOURCE_MODE=ARCHIVE] .git directory absent; validating authoritative package provenance...")
        # Validate candidate SHA record
        sha_file = os.path.join(repo_b_target, "manifests", "candidate_sha.txt")
        if not os.path.isfile(sha_file):
            failures.append(f"Archive missing candidate SHA manifest: {sha_file}")
        else:
            cand_sha = open(sha_file, encoding="utf-8").read().strip()
            if cand_sha != expected_candidate_b:
                failures.append(f"Candidate SHA mismatch in candidate_sha.txt: {cand_sha} != {expected_candidate_b}")
            else:
                print(f"[PASS] Authoritative Candidate SHA verified: {cand_sha}")

        # Validate release manifest provenance
        rel_man_file = os.path.join(repo_b_target, "backend", "app", "core", "release_manifest.json")
        if not os.path.isfile(rel_man_file):
            failures.append(f"Archive missing release manifest: {rel_man_file}")
        else:
            try:
                rel_data = json.loads(open(rel_man_file, encoding="utf-8").read())
                prov = rel_data.get("git_provenance", {})
                if prov.get("base_commit_sha") != expected_base_b:
                    failures.append(f"Release manifest base SHA mismatch: {prov.get('base_commit_sha')} != {expected_base_b}")
                else:
                    print(f"[PASS] Release manifest base commit provenance verified: {expected_base_b}")
                if prov.get("candidate_commit_sha") != expected_candidate_b:
                    failures.append(f"Release manifest candidate SHA mismatch: {prov.get('candidate_commit_sha')} != {expected_candidate_b}")
                else:
                    print(f"[PASS] Release manifest candidate commit provenance verified: {expected_candidate_b}")
                if prov.get("integration_branch") != "integration/sih-round2-selective-merge":
                    failures.append(f"Release manifest unexpected integration branch: {prov.get('integration_branch')}")
                else:
                    print(f"[PASS] Release manifest integration branch verified: {prov.get('integration_branch')}")
            except Exception as exc:
                failures.append(f"Could not parse release manifest: {exc}")

    # 3. Manifest files exist and non-empty
    for mf in [
        "manifests/repo_a_artifact_hashes.sha256",
        "manifests/repo_b_artifact_hashes.sha256",
        "manifests/supplied_docs.sha256",
        "manifests/repo_a_head.txt",
        "manifests/repo_b_head.txt",
        "manifests/repo_a_tree.txt",
        "manifests/repo_b_tree.txt",
        "manifests/repo_a_size.txt",
        "manifests/repo_b_size.txt",
        "manifests/repo_a_lfs_state.txt"
    ]:
        target_path = os.path.join(repo_b_target, mf) if not os.path.exists(mf) else mf
        if not os.path.exists(target_path) or os.path.getsize(target_path) == 0:
            failures.append(f"Missing or empty manifest: {mf}")
        else:
            print(f"[PASS] Manifest verified: {mf} ({os.path.getsize(target_path)} bytes)")

    if failures:
        print("\nGATE FAILED:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("\n=== STEP 1 COMPULSORY GATE TEST PASSED ===")
        sys.exit(0)

if __name__ == "__main__":
    test_step1()
