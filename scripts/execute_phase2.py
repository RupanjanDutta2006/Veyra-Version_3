import os
import subprocess
import csv

WORKSPACE = os.path.abspath(".")
REPO_B = os.path.join(WORKSPACE, "repos", "repo_b")
MANIFESTS = os.path.join(WORKSPACE, "manifests")

def run(cmd, cwd=None):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return res.returncode, res.stdout.strip(), res.stderr.strip()

def main():
    print("=== STARTING PHASE 2: BASE SELECTION AND BRANCH CONTROLS ===")

    # 1. Verify branch in repo_b
    code, branch, _ = run("git branch --show-current", cwd=REPO_B)
    print(f"Current branch in repo_b: {branch}")
    if branch != "integration/sih-round2-selective-merge":
        run("git switch integration/sih-round2-selective-merge", cwd=REPO_B)
        _, branch, _ = run("git branch --show-current", cwd=REPO_B)
        print(f"Switched to branch: {branch}")

    # 2. Create .github/branch-protection.md in repo_b
    github_dir = os.path.join(REPO_B, ".github")
    os.makedirs(github_dir, exist_ok=True)
    bp_path = os.path.join(github_dir, "branch-protection.md")
    bp_content = """# Veyra Repository B — Branch Protection & Integration Rules

1. **Target Branch:** `integration/sih-round2-selective-merge` is the active staging integration branch.
2. **Upstream Main:** Never push unchecked experimental code or unverified artifacts to `main`.
3. **Selective Merge Only:** Imports from Repository A must strictly adhere to `manifests/import_allowlist.csv`.
4. **Denylist Enforcement:** Files listed in `manifests/import_denylist.csv` are strictly forbidden.
5. **No Duplicate Trees:** No secondary application trees (e.g. `Builder-2`, `Parinidhi`) allowed.
6. **Compulsory Gates:** Every integration phase must pass its gate test before proceeding.
"""
    with open(bp_path, "w", encoding="utf-8") as f:
        f.write(bp_content)
    print(f"Created branch protection doc at: {bp_path}")

    # 3. Create manifests/canonical_directory_map.md
    cdm_path = os.path.join(MANIFESTS, "canonical_directory_map.md")
    cdm_content = """# Canonical Directory Mapping — Single Active Base (Repository B)

```text
backend/
├── app/
│   ├── api/            ← Versioned routes (SINGULAR authority: /v1)
│   ├── builder2/       ← Model adapter, feature pipeline (SINGULAR)
│   ├── core/           ← Core config, logging, time contract, certification policy
│   ├── data/           ← Zarr store, SQLite revision DB (SINGULAR)
│   ├── safety/         ← OOD detector, safe-fail abstention policy
│   └── services/       ← Forecasting & reliability services
├── tests/              ← All backend tests (Pytest)
frontend/
├── src/                ← React + Vite frontend application (SINGULAR)
models/
├── v3/                 ← V3 incumbent LightGBM & Isotonic calibrator (SINGULAR)
scripts/                ← Verification, test, and release automation scripts
manifests/              ← Authoritative ledgers, claim registers, release manifests
docs/                   ← Cleaned documentation & scientific guides
data/                   ← Operational topologies, reference benchmarks
```
"""
    with open(cdm_path, "w", encoding="utf-8") as f:
        f.write(cdm_content)
    print(f"Created canonical directory map at: {cdm_path}")

    # 4. Create manifests/import_allowlist.csv
    allowlist_path = os.path.join(MANIFESTS, "import_allowlist.csv")
    allowlist_entries = [
        {"source_repo": "repo_a", "source_path": "backend/app/core/time_contract.py", "destination_path": "backend/app/core/time_contract.py", "action": "adapt", "owner": "Safety Architect", "phase_gate": "Phase 4 (P4-G4)"},
        {"source_repo": "repo_a", "source_path": "backend/app/core/certification_policy.py", "destination_path": "backend/app/core/certification_policy.py", "action": "adapt", "owner": "Safety Architect", "phase_gate": "Phase 4 (P4-G5)"},
        {"source_repo": "repo_a", "source_path": "backend/app/core/ood_policy.py", "destination_path": "backend/app/core/ood_policy.py", "action": "adapt", "owner": "Safety Architect", "phase_gate": "Phase 4 (P4-G6)"},
        {"source_repo": "repo_a", "source_path": "backend/app/builder2/v3_model_adapter.py (safe-fail patterns)", "destination_path": "backend/app/builder2/v3_model_adapter.py", "action": "adapt_graft", "owner": "Model Lead", "phase_gate": "Phase 4 (P4-G4)"},
        {"source_repo": "repo_a", "source_path": "backend/app/api/v1/endpoints/predict.py (safe-fail patterns)", "destination_path": "backend/app/api/v1/endpoints/predict.py", "action": "adapt_graft", "owner": "API Lead", "phase_gate": "Phase 4 (P4-G4)"},
        {"source_repo": "repo_a", "source_path": "revision_store.py", "destination_path": "backend/app/data/revision_store.py", "action": "adapt", "owner": "Data Architect", "phase_gate": "Phase 5 (P5-G7)"},
        {"source_repo": "repo_a", "source_path": "backend/app/services/revision_service.py", "destination_path": "backend/app/services/revision_service.py", "action": "adapt", "owner": "Data Architect", "phase_gate": "Phase 5 (P5-G7)"},
        {"source_repo": "repo_a", "source_path": "backend/tests/test_v3_time_contract.py", "destination_path": "backend/tests/test_v3_time_contract.py", "action": "port", "owner": "Test Lead", "phase_gate": "Phase 4 (P4-G4)"},
        {"source_repo": "repo_a", "source_path": "test_day34_time_contract_revision_store.py", "destination_path": "backend/tests/test_day34_time_contract_revision_store.py", "action": "port", "owner": "Test Lead", "phase_gate": "Phase 5 (P5-G7)"},
        {"source_repo": "repo_a", "source_path": "test_day35_independent_replay_release_manifest.py", "destination_path": "backend/tests/test_day35_independent_replay_release_manifest.py", "action": "port", "owner": "Test Lead", "phase_gate": "Phase 5 (P5-G7)"},
        {"source_repo": "repo_a", "source_path": "test_day37_provider_adapters.py", "destination_path": "backend/tests/test_day37_provider_adapters.py", "action": "port", "owner": "Test Lead", "phase_gate": "Phase 6 (P6-G8)"},
        {"source_repo": "repo_a", "source_path": "test_day38_cross_provider_disagreement.py", "destination_path": "backend/tests/test_day38_cross_provider_disagreement.py", "action": "port", "owner": "Test Lead", "phase_gate": "Phase 6 (P6-G8)"},
        {"source_repo": "repo_a", "source_path": "test_scientific_certification.py", "destination_path": "backend/tests/test_scientific_certification.py", "action": "port", "owner": "Test Lead", "phase_gate": "Phase 4 (P4-G5)"}
    ]
    with open(allowlist_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["source_repo", "source_path", "destination_path", "action", "owner", "phase_gate"])
        writer.writeheader()
        writer.writerows(allowlist_entries)
    print(f"Created allowlist with {len(allowlist_entries)} items at: {allowlist_path}")

    # 5. Create manifests/import_denylist.csv
    denylist_path = os.path.join(MANIFESTS, "import_denylist.csv")
    denylist_entries = [
        {"source_repo": "repo_a", "path_pattern": "models/v3/*.joblib", "reason": "Git LFS pointer text, not deployable binary"},
        {"source_repo": "repo_a", "path_pattern": "Builder-2/", "reason": "Duplicate application tree"},
        {"source_repo": "repo_a", "path_pattern": "Parinidhi/", "reason": "Duplicate application tree"},
        {"source_repo": "repo_a", "path_pattern": "Frontend-Original/", "reason": "Duplicate application tree"},
        {"source_repo": "repo_a", "path_pattern": "Overview/", "reason": "Historical tree"},
        {"source_repo": "repo_a", "path_pattern": "Audits/stale_*", "reason": "Stale audit notes"},
        {"source_repo": "repo_b", "path_pattern": "models/day4/* as active model", "reason": "Baseline model only, never deploy as active V3"},
        {"source_repo": "repo_b", "path_pattern": "specialist metrics without empirical dataset", "reason": "Cannot be promoted to production without independent training"}
    ]
    with open(denylist_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["source_repo", "path_pattern", "reason"])
        writer.writeheader()
        writer.writerows(denylist_entries)
    print(f"Created denylist with {len(denylist_entries)} items at: {denylist_path}")

    # 6. Create manifests/code_owners.md
    owners_path = os.path.join(MANIFESTS, "code_owners.md")
    owners_content = """# Veyra Code Ownership Map

| Path Pattern | Owner Role | Primary Responsibility |
|---|---|---|
| `models/v3/` | Model Custodian | Artifact integrity, SHA256 hashes, feature contracts |
| `backend/app/safety/` | Safety Architect | OOD detector, safe-fail abstention, trust boundaries |
| `backend/app/core/` | System Architect | Time contracts, UTC enforcement, certification policies |
| `backend/app/data/` | Data Engineer | Zarr store, SQLite revision history, truth sealing |
| `backend/app/api/` | Backend Lead | OpenAPI routes, response schemas, versioning |
| `backend/app/builder2/` | ML Engineer | Model adapters, feature pipelines, heuristic engines |
| `frontend/src/` | Frontend Lead | User interface, provenance badges, trust banners |
| `backend/tests/` | QA & Release Lead | Test suites, regression verification, replay harness |
| `manifests/` | Release Engineer | Release manifests, audit trails, claim registers |
| `docs/` | Documentation Lead | Evidence-class alignment, honest scientific language |
"""
    with open(owners_path, "w", encoding="utf-8") as f:
        f.write(owners_content)
    print(f"Created code owners map at: {owners_path}")

    print("=== PHASE 2 SETUP COMPLETE ===")

if __name__ == "__main__":
    main()
