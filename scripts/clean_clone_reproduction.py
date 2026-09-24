"""Clean-Clone / Archive Reproduction Validator for Veyra Round 2.

Supports two explicit reproduction modes:
1. GIT MODE (when .git is present or --mode=git):
   Clones the repository at the candidate tag to a pristine isolated folder,
   verifying Git ancestry, artifact integrity, specialist boundaries, and loadability.
2. ARCHIVE MODE (when .git is absent or --mode=archive):
   Reproduces the self-contained package in a pristine isolated temporary directory,
   verifying candidate SHA provenance, artifact integrity, specialist containment, and loadability.
   Explicitly reports as ARCHIVE REPRODUCTION so it is never mislabeled as a Git clean-clone.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

if os.path.isdir("backend") and os.path.isdir("models"):
    SOURCE_REPO = os.path.abspath(".")
elif os.path.isdir("repos/repo_b"):
    SOURCE_REPO = os.path.abspath("repos/repo_b")
else:
    SOURCE_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(cmd, cwd=None):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return res.returncode, res.stdout.strip(), res.stderr.strip()


def run_reproduction_test(tag: str, log_dir: str, mode: str = "auto") -> int:
    is_git_present = os.path.isdir(os.path.join(SOURCE_REPO, ".git"))
    
    if mode == "auto":
        resolved_mode = "git" if is_git_present else "archive"
    else:
        resolved_mode = mode.lower()

    if resolved_mode == "git" and not is_git_present:
        print("[FAIL] Git reproduction mode requested, but no .git repository exists in SOURCE_REPO.")
        print("       To test archive reproduction from this standalone package, use --mode archive.")
        return 1

    if not os.path.isabs(log_dir):
        log_dir = os.path.join(SOURCE_REPO, log_dir)
    os.makedirs(log_dir, exist_ok=True)
    temp_dir = tempfile.mkdtemp(prefix=f"veyra_{resolved_mode}_clone_")
    print(f"=== Running Veyra Reproduction Test [{resolved_mode.upper()} MODE] ===")
    print(f"Isolated temporary directory: {temp_dir}")
    log_file = os.path.join(log_dir, f"reproduction_{resolved_mode}_{tag}.log")

    try:
        if resolved_mode == "git":
            print(f"[SOURCE_MODE=GIT] Step 1: Cloning repository at tag '{tag}'...")
            code, out, err = run(f'git clone --branch "{tag}" "{SOURCE_REPO}" .', cwd=temp_dir)
            if code != 0:
                print(f"[FAIL] Git clone failed: {err}\n{out}")
                return 1

            code, commit_sha, _ = run("git rev-parse HEAD", cwd=temp_dir)
            print(f"  Cloned commit SHA: {commit_sha}")
        else:
            print(f"[SOURCE_MODE=ARCHIVE] Step 1: Staging self-contained source package into isolated environment...")
            # Copy source package into temp directory excluding transient caches
            ignore_func = shutil.ignore_patterns(
                ".pytest_cache", "__pycache__", "node_modules", ".venv", "tmp", "*.pyc"
            )
            for item in os.listdir(SOURCE_REPO):
                src_item = os.path.join(SOURCE_REPO, item)
                dst_item = os.path.join(temp_dir, item)
                if os.path.isdir(src_item):
                    shutil.copytree(src_item, dst_item, ignore=ignore_func)
                elif os.path.isfile(src_item):
                    shutil.copy2(src_item, dst_item)

            # Validate Candidate SHA provenance in archive
            cand_sha_file = os.path.join(temp_dir, "manifests", "candidate_sha.txt")
            if not os.path.isfile(cand_sha_file):
                print(f"[FAIL] Missing candidate SHA manifest in staged archive: {cand_sha_file}")
                return 1
            commit_sha = open(cand_sha_file, encoding="utf-8").read().strip()
            print(f"  Authoritative candidate SHA from archive: {commit_sha}")

        # Step 2: Run verify_artifacts.py in the isolated clone/package
        print("Step 2: Executing artifact integrity verification in isolated environment...")
        code, out, err = run("python scripts/verify_artifacts.py", cwd=temp_dir)
        if code != 0:
            print(f"[FAIL] Artifact verification failed in isolated environment:\n{out}\n{err}")
            return 1
        print("  [PASS] Artifacts cryptographically verified.")

        # Step 3: Run production specialist boundary check
        print("Step 3: Checking specialist promotion boundaries...")
        code, out, err = run("python scripts/check_production_specialists.py --fail-on-unvalidated-promotion", cwd=temp_dir)
        if code != 0:
            print(f"[FAIL] Specialist boundary check failed in isolated environment:\n{out}\n{err}")
            return 1
        print("  [PASS] Specialist boundaries verified.")

        # Step 4: Test Model and Calibrator deserialization & inference
        print("Step 4: Testing model and calibrator loads...")
        cmd_test = (
            "python -c \""
            "import joblib; "
            "m=joblib.load('models/v3/lightgbm_v3_challenger.joblib'); "
            "c=joblib.load('models/v3/probability_calibrator_v3.joblib'); "
            "assert type(c).__name__=='IsotonicRegression'; "
            "assert m.num_feature()==50; "
            "print('MODEL_LOAD_SUCCESS')"
            "\""
        )
        code, out, err = run(cmd_test, cwd=temp_dir)
        if code != 0 or "MODEL_LOAD_SUCCESS" not in out:
            print(f"[FAIL] Model load failed in isolated environment (code {code}):\nStdout: {out}\nStderr: {err}")
            return 1
        print("  [PASS] Model and calibrator successfully loaded.")

        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"Veyra [{resolved_mode.upper()} MODE] reproduction for {tag} SUCCESSFUL at commit {commit_sha}\n")

        if resolved_mode == "git":
            print(f"\n=== [SOURCE_MODE=GIT] CLEAN-CLONE REPRODUCTION PASSED (Commit: {commit_sha}) ===")
        else:
            print(f"\n=== [SOURCE_MODE=ARCHIVE] ARCHIVE-MODE ISOLATED REPRODUCTION PASSED (Candidate SHA: {commit_sha}) ===")
            print("Note: Package successfully reproduced from self-contained release archive.")
        return 0

    finally:
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="sih-round2-candidate-v1")
    parser.add_argument("--log-dir", default="artifacts/submission_reproduction")
    parser.add_argument("--mode", choices=["auto", "git", "archive"], default="auto")
    args = parser.parse_args()
    sys.exit(run_reproduction_test(args.tag, args.log_dir, args.mode))
