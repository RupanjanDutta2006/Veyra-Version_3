import os
import subprocess
import hashlib
import json
import csv

WORKSPACE = os.path.abspath(".")
MANIFESTS = os.path.join(WORKSPACE, "manifests")
LOGS = os.path.join(WORKSPACE, "logs")
REPOS = os.path.join(WORKSPACE, "repos")
REPO_A = os.path.join(REPOS, "repo_a")
REPO_B = os.path.join(REPOS, "repo_b")

def run(cmd, cwd=None):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return res.returncode, res.stdout.strip(), res.stderr.strip()

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def step0_1_audit_state():
    print("Executing Step 0.1: Audit State Manifests...")
    for repo_name, repo_dir in [("repo_a", REPO_A), ("repo_b", REPO_B)]:
        _, out, _ = run("git log -1 --format='SHA:%H%nDate:%cI%nSubject:%s%nBranch:%D'", cwd=repo_dir)
        dest = os.path.join(MANIFESTS, f"{repo_name}_audit_state.txt")
        with open(dest, "w", encoding="utf-8") as f:
            f.write(out + "\n")
    print("  Done: repo_a_audit_state.txt and repo_b_audit_state.txt")

def step0_2_repo_metadata():
    print("Executing Step 0.2: Repository Metadata...")
    lines = []
    for repo_name, repo_dir in [("repo_a", REPO_A), ("repo_b", REPO_B)]:
        lines.append(f"=== {repo_name} ===")
        _, branch, _ = run("git branch --show-current", cwd=repo_dir)
        lines.append(f"Branch: {branch}")
        _, date, _ = run("git log -1 --format='%cI'", cwd=repo_dir)
        lines.append(f"Commit Date: {date}")
        _, remote, _ = run("git remote get-url origin", cwd=repo_dir)
        lines.append(f"Remote URL: {remote}")
        _, status, _ = run("git status --porcelain", cwd=repo_dir)
        lines.append(f"Status: {'clean' if not status else status}")
        _, count, _ = run("git rev-list --count HEAD", cwd=repo_dir)
        lines.append(f"History Commit Count: {count}")
        _, tags, _ = run("git tag -l", cwd=repo_dir)
        lines.append(f"Tags: {tags.replace(chr(10), ', ')}")
        lines.append("")
    dest = os.path.join(MANIFESTS, "repo_metadata.txt")
    with open(dest, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("  Done: repo_metadata.txt")

def step0_3_path_inventories():
    print("Executing Step 0.3: Path Inventories...")
    deploy_exts = {".yml", ".yaml", "Dockerfile", "Dockerfile.dev", "Dockerfile.prod", "vercel.json"}
    
    for repo_name, repo_dir in [("repo_a", REPO_A), ("repo_b", REPO_B)]:
        full_tree = []
        backend_files = []
        frontend_files = []
        model_files = []
        test_files = []
        script_files = []
        doc_files = []
        data_files = []
        deploy_files = []

        for root, dirs, files in os.walk(repo_dir):
            if ".git" in root.split(os.sep):
                continue
            for file in sorted(files):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, repo_dir).replace("\\", "/")
                entry = f"./{rel_path}\n"
                full_tree.append(entry)

                p_lower = rel_path.lower()
                if "backend/" in p_lower:
                    backend_files.append(entry)
                if "frontend/" in p_lower:
                    frontend_files.append(entry)
                if "models/" in p_lower or p_lower.endswith(".joblib"):
                    model_files.append(entry)
                if "tests/" in p_lower or "test/" in p_lower or file.startswith("test_") or file.endswith("_test.py") or file.endswith(".test.ts") or file.endswith(".test.tsx"):
                    test_files.append(entry)
                if "scripts/" in p_lower or file.endswith(".sh") or file.endswith(".bat"):
                    script_files.append(entry)
                if "docs/" in p_lower or p_lower.endswith(".md") or p_lower.endswith(".rst") or p_lower.endswith(".txt"):
                    doc_files.append(entry)
                if "data/" in p_lower or "fixtures/" in p_lower or p_lower.endswith(".parquet") or p_lower.endswith(".zarr"):
                    data_files.append(entry)
                if any(file.endswith(x) or file == x for x in deploy_exts) or "workflow" in p_lower or "docker" in p_lower:
                    deploy_files.append(entry)

        def write_list(fname, items):
            items.sort()
            with open(os.path.join(MANIFESTS, f"{repo_name}_{fname}"), "w", encoding="utf-8") as f:
                f.writelines(items)

        write_list("full_tree.txt", full_tree)
        write_list("backend_files.txt", backend_files)
        write_list("frontend_files.txt", frontend_files)
        write_list("model_files.txt", model_files)
        write_list("test_files.txt", test_files)
        write_list("script_files.txt", script_files)
        write_list("doc_files.txt", doc_files)
        write_list("data_files.txt", data_files)
        write_list("deploy_files.txt", deploy_files)
        print(f"  Done {repo_name}: {len(full_tree)} total tracked/unignored files categorized.")

def step0_4_critical_artifact_hashes():
    print("Executing Step 0.4: Computing Critical Artifact Hashes...")
    exts = {".joblib", ".json", ".yaml", ".yml", ".lock", ".toml"}
    special_names = {"requirements.txt", "pyproject.toml", "Dockerfile"}

    for repo_name, repo_dir in [("repo_a", REPO_A), ("repo_b", REPO_B)]:
        entries = []
        for root, dirs, files in os.walk(repo_dir):
            if ".git" in root.split(os.sep):
                continue
            for file in sorted(files):
                _, ext = os.path.splitext(file)
                if ext.lower() in exts or file.lower() in special_names or file.lower().startswith("requirements"):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, repo_dir).replace("\\", "/")
                    try:
                        h = sha256_file(full_path)
                        entries.append(f"{h}  {rel_path}\n")
                    except Exception as e:
                        entries.append(f"# ERROR {rel_path}: {e}\n")
        entries.sort()
        dest = os.path.join(MANIFESTS, f"{repo_name}_artifact_hashes.sha256")
        with open(dest, "w", encoding="utf-8") as f:
            f.writelines(entries)
        print(f"  Done {repo_name}: {len(entries)} artifacts hashed in {repo_name}_artifact_hashes.sha256")

def step0_5_file_classifications():
    print("Executing Step 0.5: Classifying File Types...")
    classifications = []
    
    for repo_name, repo_dir in [("repo_a", REPO_A), ("repo_b", REPO_B)]:
        for root, dirs, files in os.walk(repo_dir):
            if ".git" in root.split(os.sep):
                continue
            for file in sorted(files):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, repo_dir).replace("\\", "/")
                sha = sha256_file(full_path)
                size = os.path.getsize(full_path)
                
                # Classify
                classification = "code"
                notes = ""
                
                if rel_path.endswith(".joblib"):
                    # Check if pointer or real binary
                    if size < 500:
                        classification = "pointer_text"
                        notes = "Git LFS pointer text (not loadable)"
                    else:
                        classification = "real_payload"
                        notes = "Loadable serialized binary model/calibrator"
                elif rel_path.endswith(".md") or rel_path.endswith(".txt") or "/docs/" in rel_path:
                    classification = "documentation"
                elif "fixtures" in rel_path or "test_data" in rel_path or "/mock" in rel_path or "golden" in rel_path:
                    classification = "fixture"
                elif rel_path.endswith(".json") and ("manifest" in rel_path or "config" in rel_path or "features" in rel_path or "topology" in rel_path or "report" in rel_path):
                    classification = "manifest_config"
                elif "test" in rel_path or file.startswith("test_"):
                    classification = "test"
                elif "scripts/" in rel_path:
                    classification = "script"
                elif "Builder-2/" in rel_path or "Parinidhi/" in rel_path or "Frontend-Original/" in rel_path or "Overview/" in rel_path:
                    classification = "duplicate_tree"
                    notes = "Historical noncanonical duplicate tree in Repo A"
                
                classifications.append({
                    "repo": repo_name,
                    "path": rel_path,
                    "size_bytes": size,
                    "classification": classification,
                    "sha256": sha,
                    "notes": notes
                })

    dest = os.path.join(MANIFESTS, "file_classifications.csv")
    with open(dest, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["repo", "path", "size_bytes", "classification", "sha256", "notes"])
        writer.writeheader()
        writer.writerows(classifications)
    print(f"  Done: Classified {len(classifications)} files into file_classifications.csv")

def step0_6_preserve_baseline_logs():
    print("Executing Step 0.6: Preserving Baseline Logs...")
    os.makedirs(os.path.join(LOGS, "repo_a_baseline"), exist_ok=True)
    os.makedirs(os.path.join(LOGS, "repo_b_baseline"), exist_ok=True)
    
    # Run pytest collection on both repos and record baseline
    for repo_name, repo_dir in [("repo_a", REPO_A), ("repo_b", REPO_B)]:
        dest_log = os.path.join(LOGS, f"{repo_name}_baseline", "pytest_collect.log")
        code, out, err = run("python -m pytest --collect-only -q", cwd=repo_dir)
        with open(dest_log, "w", encoding="utf-8") as f:
            f.write(f"Return code: {code}\nSTDOUT:\n{out}\nSTDERR:\n{err}\n")
        print(f"  Baseline pytest collect for {repo_name} saved to {dest_log}")

def step0_7_asset_ledger():
    print("Executing Step 0.7: Creating Asset Ledger...")
    # Read classification and create ledger
    ledger_entries = []

    # Known key rules from 12_asset_collection_plan.md:
    rules_a = {
        "models/v3/lightgbm_v3_challenger.joblib": ("reject", "Quarantined pointer text; use Repo B binary", "P3-G1"),
        "models/v3/probability_calibrator_v3.joblib": ("reject", "Quarantined pointer text; use Repo B binary", "P3-G1"),
        "models/v3/feature_names.json": ("adapt", "Informative/adapt - compare with B", "P3-G2"),
        "backend/app/core/time_contract.py": ("adapt", "Selective safety graft - UTC enforcement", "P4-G4"),
        "revision_store.py": ("adapt", "Durable revision store patterns", "P5-G7"),
        "backend/app/services/revision_service.py": ("adapt", "Revision service patterns", "P5-G7"),
        "backend/app/core/certification_policy.py": ("adapt", "Scientific boundary - certification disclaimer", "P1-G0"),
        "backend/app/core/ood_policy.py": ("adapt", "OOD abstention policy patterns", "P4-G6"),
        "backend/app/core/replay_harness.py": ("adapt", "Replay harness patterns", "P5-G7"),
        "golden_replay_matrix.py": ("adapt", "Replay test matrix", "P5-G7"),
        "backend/tests/test_v3_time_contract.py": ("port", "Port time contract unit test", "P4-G4"),
        "test_day34_time_contract_revision_store.py": ("port", "Port revision store integration test", "P5-G7"),
        "test_day35_independent_replay_release_manifest.py": ("port", "Port independent replay test", "P5-G7"),
        "test_day37_provider_adapters.py": ("port", "Port provider adapter test", "P6-G8"),
        "test_day38_cross_provider_disagreement.py": ("port", "Port disagreement test", "P6-G8"),
        "test_scientific_certification.py": ("port", "Port certification boundary test", "P1-G0"),
        "Builder-2": ("reject", "Duplicate application tree", "P0-G0"),
        "Parinidhi": ("reject", "Duplicate application tree", "P0-G0"),
        "Frontend-Original": ("reject", "Historical duplicate frontend", "P0-G0"),
        "Overview": ("reject", "Historical folder", "P0-G0"),
    }

    # Populate ledger for Repo A
    for root, dirs, files in os.walk(REPO_A):
        if ".git" in root.split(os.sep):
            continue
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, REPO_A).replace("\\", "/")
            sha = sha256_file(full_path)
            
            action = "informative"
            notes = "Reference evidence only"
            gate = "P0-G0"
            dest_path = f"imported_from_a/{rel_path}"
            
            for prefix, (act, n, g) in rules_a.items():
                if rel_path == prefix or rel_path.startswith(prefix + "/"):
                    action = act
                    notes = n
                    gate = g
                    if act == "reject":
                        dest_path = "REJECTED"
                    break
                    
            ledger_entries.append({
                "source_repo": "repo_a",
                "source_path": rel_path,
                "source_sha256": sha,
                "destination_path": dest_path,
                "action": action,
                "owner": "Integration Architect",
                "validation_gate": gate,
                "notes": notes
            })

    # Populate ledger for Repo B (Base repo)
    for root, dirs, files in os.walk(REPO_B):
        if ".git" in root.split(os.sep):
            continue
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, REPO_B).replace("\\", "/")
            sha = sha256_file(full_path)
            
            action = "keep"
            notes = "Canonical base asset"
            gate = "P2-G0"
            dest_path = rel_path
            
            if rel_path == "models/v3/feature_names.json":
                action = "repair"
                notes = "Feature checksum mismatch repair required in Phase 3"
                gate = "P3-G2"
            elif "specialist" in rel_path or "spatial_reliability_engine" in rel_path or "compound_hazard" in rel_path:
                action = "quarantine_experimental"
                notes = "Keep as experimental module; do not promote without empirical dataset"
                gate = "P6-G8"
            elif rel_path.startswith("models/day4/") or "baseline_logistic" in rel_path:
                action = "keep_baseline"
                notes = "Legacy comparison baseline only; do not deploy as active model"
                gate = "P3-G3"

            ledger_entries.append({
                "source_repo": "repo_b",
                "source_path": rel_path,
                "source_sha256": sha,
                "destination_path": dest_path,
                "action": action,
                "owner": "Integration Architect",
                "validation_gate": gate,
                "notes": notes
            })

    dest = os.path.join(MANIFESTS, "asset_ledger.csv")
    with open(dest, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "source_repo", "source_path", "source_sha256", "destination_path", "action", "owner", "validation_gate", "notes"
        ])
        writer.writeheader()
        writer.writerows(ledger_entries)
    print(f"  Done: {len(ledger_entries)} entries written to asset_ledger.csv")

def step0_8_duplicate_trees():
    print("Executing Step 0.8: Recording Duplicate Trees in Repo A...")
    dup_info = {
        "Builder-2": {
            "status": "historical_noncanonical",
            "reason": "Duplicate backend/model tree from intermediate hackathon stage. Contains outdated requirements and redundant endpoints.",
            "disposition": "REJECT - do not merge into base repo."
        },
        "Parinidhi": {
            "status": "historical_noncanonical",
            "reason": "Duplicate application tree containing patch scripts (_v4_patch, _v5_patch) and older frontend copies.",
            "disposition": "REJECT - do not merge into base repo."
        },
        "Frontend-Original": {
            "status": "historical_noncanonical",
            "reason": "Original legacy React frontend superseded by repo_b frontend implementation.",
            "disposition": "REJECT - do not merge into base repo."
        },
        "Overview": {
            "status": "historical_noncanonical",
            "reason": "Temporary evaluation notes and partial mock logs.",
            "disposition": "REJECT - do not merge into base repo."
        }
    }
    dest = os.path.join(MANIFESTS, "duplicate_trees.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(dup_info, f, indent=2)
    print("  Done: duplicate_trees.json")

def step0_9_audit_scores():
    print("Executing Step 0.9: Freezing Audit Scores...")
    scores_path = os.path.join(WORKSPACE, "docs", "score_data.csv")
    categories = []
    total_a_raw, total_a_weighted = 0.0, 0.0
    total_b_raw, total_b_weighted = 0.0, 0.0

    if os.path.exists(scores_path):
        with open(scores_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                w = float(row["weight"])
                ar = float(row["repo_a_raw"])
                aw = float(row["repo_a_weighted"])
                br = float(row["repo_b_raw"])
                bw = float(row["repo_b_weighted"])
                categories.append({
                    "category": row["category"],
                    "weight": w,
                    "repo_a_raw": ar,
                    "repo_a_weighted": aw,
                    "repo_b_raw": br,
                    "repo_b_weighted": bw
                })
                total_a_weighted += aw
                total_b_weighted += bw
    
    score_doc = {
        "repo_a": {
            "url": "https://github.com/RupanjanDutta2006/Veyra-Know-When-Forecasts-May-Fail",
            "sha": "b9f52d3eeec8676e06b1879f05b404605e2501be",
            "weighted_score": round(total_a_weighted, 2),
            "status": "READ_ONLY_SOURCE"
        },
        "repo_b": {
            "url": "https://github.com/adishxm/Veyra-Know-When-Forecasts-May-Fail-VERSION-2",
            "sha": "82eded8194151e37fb9b3eecf273010dc62d7b29",
            "weighted_score": round(total_b_weighted, 2),
            "status": "BASE_REPOSITORY"
        },
        "categories": categories
    }

    dest = os.path.join(MANIFESTS, "audit_scores.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(score_doc, f, indent=2)
    print(f"  Done: audit_scores.json (Repo A: {score_doc['repo_a']['weighted_score']}, Repo B: {score_doc['repo_b']['weighted_score']})")

def main():
    print("=== STARTING PHASE 0: FREEZE AND INVENTORY ===")
    step0_1_audit_state()
    step0_2_repo_metadata()
    step0_3_path_inventories()
    step0_4_critical_artifact_hashes()
    step0_5_file_classifications()
    step0_6_preserve_baseline_logs()
    step0_7_asset_ledger()
    step0_8_duplicate_trees()
    step0_9_audit_scores()
    print("=== PHASE 0 EXECUTION COMPLETE ===")

if __name__ == "__main__":
    main()
