# Implementation Plan — Phase 0: Freeze and Inventory

## Objective

Freeze both audited repository states and create an immutable evidence baseline before any integration edit touches either codebase.

## Entry Criteria

- [ ] Step 1 complete: both repos cloned, SHAs verified, workspace created
- [ ] Read-only clones available with clean worktrees
- [ ] Two audited SHAs recorded: A=`b9f52d3`, B=`82eded8`
- [ ] Supplied documentation archive preserved and hashed
- [ ] No integration branch created from unrecorded working-tree changes

## Inputs

### From Repository A (SHA `b9f52d3`)
| File/Path | Purpose |
|---|---|
| `models/v3/feature_names.json` | Feature schema reference |
| `models/v3/lightgbm_v3_challenger.joblib` | **Pointer-file evidence only** (NOT deployable) |
| `models/v3/probability_calibrator_v3.joblib` | **Pointer-file evidence only** (NOT deployable) |
| `training_manifest.json` | Training provenance |
| `v3_evaluation_manifest.json` | Evaluation provenance |
| `backend/app/core/release_manifest.*` | Release manifest patterns |
| `backend/app/builder2/v3_model_adapter.py` | Model adapter reference |
| `backend/app/builder2/v3_feature_pipeline.py` | Feature pipeline reference |
| `backend/app/api/v1/endpoints/predict.py` | Predict endpoint reference |
| Test and build logs | Baseline evidence |

### From Repository B (SHA `82eded8`)
| File/Path | Purpose |
|---|---|
| `models/v3/lightgbm_v3_challenger.joblib` | **Loadable V3 model** (canonical) |
| `models/v3/probability_calibrator_v3.joblib` | **Loadable calibrator** (canonical) |
| `models/v3/feature_names.json` | Feature schema (needs checksum repair) |
| `artifact_manifest.json` | Artifact provenance |
| `training_manifest.json` | Training provenance |
| `v3_evaluation_manifest.json` | Evaluation provenance |
| `v3_comprehensive_evaluation.json` | Comprehensive evaluation data |
| `models/day4/*`, `models/baseline_logistic_v1*` | Legacy baseline models |
| `backend/app/builder2/v3_model_adapter.py` | Model adapter (destination) |
| `scripts/verify_artifacts.py` | Artifact verifier script |
| Backend/frontend test and build logs | Baseline evidence |

## Implementation Steps

### Step 0.1 — Create Read-Only Tags/Archive References

```bash
cd "$WORKSPACE/repos"
# Tags should already exist from Step 1, verify:
git -C repo_a tag -l 'audit-*'
git -C repo_b tag -l 'audit-*'

# Create archive manifests
git -C repo_a log -1 --format='SHA:%H%nDate:%cI%nSubject:%s%nBranch:%D' > "$WORKSPACE/manifests/repo_a_audit_state.txt"
git -C repo_b log -1 --format='SHA:%H%nDate:%cI%nSubject:%s%nBranch:%D' > "$WORKSPACE/manifests/repo_b_audit_state.txt"
```

### Step 0.2 — Record Repository Metadata

For each repository, record:
- Default branch name
- Commit timestamp
- Remote URL
- Working-tree status (`git status --porcelain`)
- Visible history depth (`git rev-list --count HEAD`)

```bash
for repo in repo_a repo_b; do
  echo "=== $repo ===" >> "$WORKSPACE/manifests/repo_metadata.txt"
  git -C "$WORKSPACE/repos/$repo" branch --show-current >> "$WORKSPACE/manifests/repo_metadata.txt"
  git -C "$WORKSPACE/repos/$repo" log -1 --format='%cI' >> "$WORKSPACE/manifests/repo_metadata.txt"
  git -C "$WORKSPACE/repos/$repo" remote get-url origin >> "$WORKSPACE/manifests/repo_metadata.txt"
  git -C "$WORKSPACE/repos/$repo" status --porcelain >> "$WORKSPACE/manifests/repo_metadata.txt"
  git -C "$WORKSPACE/repos/$repo" rev-list --count HEAD >> "$WORKSPACE/manifests/repo_metadata.txt"
  echo "" >> "$WORKSPACE/manifests/repo_metadata.txt"
done
```

### Step 0.3 — Complete Path Inventory

Produce complete inventories for: code, models, calibrators, manifests, tests, scripts, docs, deployment, data.

```bash
for repo in repo_a repo_b; do
  cd "$WORKSPACE/repos/$repo"
  find . -type f | sort > "$WORKSPACE/manifests/${repo}_full_tree.txt"
  
  # Categorized inventories
  find . -path '*/backend/*' -type f | sort > "$WORKSPACE/manifests/${repo}_backend_files.txt"
  find . -path '*/frontend/*' -type f | sort > "$WORKSPACE/manifests/${repo}_frontend_files.txt"
  find . -path '*/models/*' -type f | sort > "$WORKSPACE/manifests/${repo}_model_files.txt"
  find . -path '*/tests/*' -o -path '*/test/*' -type f | sort > "$WORKSPACE/manifests/${repo}_test_files.txt"
  find . -path '*/scripts/*' -type f | sort > "$WORKSPACE/manifests/${repo}_script_files.txt"
  find . -path '*/docs/*' -o -name '*.md' -type f | sort > "$WORKSPACE/manifests/${repo}_doc_files.txt"
  find . -path '*/data/*' -type f | sort > "$WORKSPACE/manifests/${repo}_data_files.txt"
  find . -name '*.yml' -o -name '*.yaml' -o -name 'Dockerfile*' -o -name 'vercel.json' | sort > "$WORKSPACE/manifests/${repo}_deploy_files.txt"
done
```

### Step 0.4 — Compute SHA256 for All Critical Artifacts

```bash
for repo in repo_a repo_b; do
  cd "$WORKSPACE/repos/$repo"
  find . -type f \( \
    -name '*.joblib' -o \
    -name '*.json' -o \
    -name '*.yaml' -o \
    -name '*.yml' -o \
    -name '*.lock' -o \
    -name 'requirements*.txt' -o \
    -name 'pyproject.toml' \
  \) -print0 | sort -z | xargs -0 sha256sum > "$WORKSPACE/manifests/${repo}_artifact_hashes.sha256"
done
```

### Step 0.5 — Classify File Types

For each file, record whether it is:
- **Real payload** — loadable binary model/calibrator
- **Pointer text** — Git LFS pointer (not deployable)
- **Fixture** — test fixture or sample data
- **Generated output** — build output, compiled asset
- **Documentation** — markdown, text docs

Create `manifests/file_classifications.csv` with columns: `repo,path,classification,sha256,notes`

### Step 0.6 — Preserve Audit Test Logs

Copy all test execution logs, warnings, runtimes, failures, skipped tests, and errors to `$WORKSPACE/logs/`:

```bash
mkdir -p "$WORKSPACE/logs/repo_a_baseline" "$WORKSPACE/logs/repo_b_baseline"
# Copy any existing test output from the audit
```

### Step 0.7 — Create Source-to-Destination Ledger

Create `manifests/asset_ledger.csv` with columns:

| Column | Description |
|---|---|
| `source_repo` | A or B |
| `source_path` | File path in source repo |
| `source_sha256` | Hash of source file |
| `destination_path` | Target path in integration branch |
| `action` | keep / adapt / port / reject / quarantine |
| `owner` | Who is responsible |
| `validation_gate` | Required gate before use |
| `notes` | Additional context |

### Step 0.8 — Record Duplicate Trees in Repository A

Repository A contains historical/duplicate application trees that must NOT be imported:

- `Builder-2/`
- `Parinidhi/`
- `Frontend-Original/`
- `Overview/`

Mark each as **historical/noncanonical** until proven otherwise.

### Step 0.9 — Freeze Comparison Scores

Record the current audit scores:

| Repository | Weighted Score |
|---|---|
| A | 47.90/100 |
| B | 65.48/100 |

Save `manifests/audit_scores.json` with all 13-category breakdown.

### Step 0.10 — Create Integration Branch (if not done in Step 1)

```bash
cd "$WORKSPACE/repos/repo_b"
git switch -c integration/sih-round2-selective-merge 2>/dev/null || git switch integration/sih-round2-selective-merge
git status --short
```

## Outputs Checklist

- [ ] Signed/integrity-protected inventory for both repos
- [ ] SHA/path ledger for both repositories (`manifests/*_artifact_hashes.sha256`)
- [ ] Candidate asset ledger (`manifests/asset_ledger.csv`)
- [ ] Baseline test/build/runtime evidence bundle (`logs/`)
- [ ] Immutable audit snapshot (tags + metadata files)
- [ ] File classification record
- [ ] Duplicate tree disposition

## Failure Conditions — Immediate Stop If:

| Condition | Why It Matters |
|---|---|
| Any source or artifact changed without a new hash and reason | Breaks evidence chain |
| Missing audit logs | Cannot compare before/after |
| Ambiguous source of a copied file | Integrity violation |
| A pointer file recorded as a deployable model | Would cause runtime failure |

## Gate P0-0

**The inventory must reproduce the two audited SHAs and must identify every:**
- model
- calibrator
- feature schema
- manifest
- test root
- deployment file
- duplicate application tree

## Compulsory Gate Test

```bash
set -euo pipefail
test "$(git -C repos/repo_a status --porcelain)" = ""
test "$(git -C repos/repo_b status --porcelain)" = ""
git -C repos/repo_a rev-parse HEAD | grep -q '^b9f52d3eeec8676e06b1879f05b404605e2501be$'
git -C repos/repo_b rev-parse HEAD | grep -q '^82eded8194151e37fb9b3eecf273010dc62d7b29$'
test -s manifests/repo_a_artifact_hashes.sha256
test -s manifests/repo_b_artifact_hashes.sha256
```

**Pass condition:** Both clean-checkout inventories, SHAs, and artifact-hash manifests exist and match frozen evidence.

---

**Previous:** [Step 1 — Clone and Workspace](01_step1_clone_and_workspace.md)  
**Next:** [Phase 1 — Truth Alignment](03_phase1_truth_alignment.md)
