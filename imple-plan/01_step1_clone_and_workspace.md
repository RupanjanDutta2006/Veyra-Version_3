# Implementation Plan — Step 1: Clone Both Repositories & Create Audit Workspace

## Objective

Clone both repositories into separate directories, preserve upstream state, and create the audit workspace with isolated environments before any integration work begins.

## Why This Step Matters

This is the foundation step. Every subsequent phase depends on having clean, recorded, unmodified clones. Skipping this or doing it carelessly will invalidate all downstream integrity checks.

## Prerequisites

- Git installed and configured
- Python 3.10+ available
- Node.js 18+ and npm/pnpm available
- Git LFS installed (for recording pointer state, NOT for pulling binaries)
- Clean shell with no prior workspace contamination

## Repository Details

| Repository | URL | Expected Branch | Expected SHA |
|---|---|---|---|
| A (Read-only source) | `https://github.com/RupanjanDutta2006/Veyra-Know-When-Forecasts-May-Fail` | `main` | `b9f52d3eeec8676e06b1879f05b404605e2501be` |
| B (Destination base) | `https://github.com/adishxm/Veyra-Know-When-Forecasts-May-Fail-VERSION-2` | `main` | `82eded8194151e37fb9b3eecf273010dc62d7b29` |

## Implementation Steps

### 1.1 Create the Workspace Directory Structure

```bash
set -euo pipefail

export WORKSPACE="$HOME/veyra-sih-round2"
rm -rf "$WORKSPACE"
mkdir -p "$WORKSPACE"/{repos,artifacts,logs,docs,manifests,builds}
cd "$WORKSPACE"
```

**Output:** Clean workspace at `~/veyra-sih-round2/` with subdirectories.

### 1.2 Clone Both Repositories Separately

```bash
cd "$WORKSPACE/repos"

git clone https://github.com/RupanjanDutta2006/Veyra-Know-When-Forecasts-May-Fail repo_a
git clone https://github.com/adishxm/Veyra-Know-When-Forecasts-May-Fail-VERSION-2 repo_b

# Record state
git -C repo_a remote -v
git -C repo_b remote -v
git -C repo_a branch --show-current
git -C repo_b branch --show-current
git -C repo_a rev-parse HEAD
git -C repo_b rev-parse HEAD
```

**Verification:** Both SHAs must match the expected values above. If either remote has moved, record the new SHA with timestamp and reason.

### 1.3 Preserve Cloned States with Tags

```bash
cd "$WORKSPACE/repos"
git -C repo_a status --short
git -C repo_b status --short
git -C repo_a log -1 --format='%H%n%cI%n%s' > "$WORKSPACE/manifests/repo_a_head.txt"
git -C repo_b log -1 --format='%H%n%cI%n%s' > "$WORKSPACE/manifests/repo_b_head.txt"
git -C repo_a tag -a audit-repo-a-b9f52d3 -m 'Frozen SIH Round-2 audit state' b9f52d3eeec8676e06b1879f05b404605e2501be
git -C repo_b tag -a audit-repo-b-82eded8 -m 'Frozen SIH Round-2 audit state' 82eded8194151e37fb9b3eecf273010dc62d7b29
```

**Rule:** Never rewrite either upstream `main` branch.

### 1.4 Check Git LFS and Record Artifact State

Repository A's V3 model files are Git LFS pointer text (NOT loadable binaries). This must be recorded.

```bash
git lfs version || true
git -C "$WORKSPACE/repos/repo_a" lfs ls-files || true
file "$WORKSPACE/repos/repo_a/models/v3/lightgbm_v3_challenger.joblib" || true
file "$WORKSPACE/repos/repo_a/models/v3/probability_calibrator_v3.joblib" || true
sha256sum "$WORKSPACE/repos/repo_a/models/v3/lightgbm_v3_challenger.joblib" || true
sha256sum "$WORKSPACE/repos/repo_a/models/v3/probability_calibrator_v3.joblib" || true
```

**CRITICAL:** Do NOT run `git lfs pull` and treat the result as the same evidence. A recovered payload is a new artifact requiring provenance and revalidation.

### 1.5 Create Documentation & Evidence Bundle

```bash
# Copy supplied docs to workspace
# (place MASTER PROMPT, research pack, 500-test suite, blueprint, etc. under $WORKSPACE/docs)

find "$WORKSPACE/docs" -type f -print0 | sort -z | xargs -0 sha256sum > "$WORKSPACE/manifests/supplied_docs.sha256"
```

**Rule:** Do not double-count duplicate copies. Select one authoritative copy per document.

### 1.6 Inventory Both Repositories Before Any Editing

```bash
for repo in repo_a repo_b; do
  (
    cd "$WORKSPACE/repos/$repo"
    find . -maxdepth 3 -type f | sort > "$WORKSPACE/manifests/${repo}_tree.txt"
    find . -type f \( -name '*.joblib' -o -name '*.json' -o -name '*.yaml' -o -name '*.yml' -o -name '*.lock' \) -print0 | sort -z | xargs -0 sha256sum > "$WORKSPACE/manifests/${repo}_artifact_hashes.sha256" || true
    du -sh . > "$WORKSPACE/manifests/${repo}_size.txt"
  )
done
```

**Output:** `manifests/repo_a_tree.txt`, `manifests/repo_b_tree.txt`, artifact hash files, size files.

### 1.7 Create the Destination Integration Branch

```bash
cd "$WORKSPACE/repos/repo_b"
git switch -c integration/sih-round2-selective-merge
git status --short
```

**Rule:** Repository A remains read-only. Repository B is the ONLY application destination.

### 1.8 Install Dependencies in Isolated Environments

```bash
python3 -m venv "$WORKSPACE/builds/repo_a_venv"
python3 -m venv "$WORKSPACE/builds/repo_b_venv"
python3 -m venv "$WORKSPACE/builds/integration_venv"
source "$WORKSPACE/builds/integration_venv/bin/activate"
python -m pip install --upgrade pip
```

**Rule:** Install only from declared requirements/lock files after the clean inventory.

### 1.9 Reproduce Before Merge

Run all available tests, builds, and smoke checks in the original checkouts BEFORE any merge:

- Artifact verification
- Test collection and execution
- Frontend build
- Startup smoke
- Release/replay commands

Save all output under `$WORKSPACE/logs`.

## Exit Criteria Checklist

- [ ] Both repositories cloned separately
- [ ] Default branches and SHAs recorded in `manifests/`
- [ ] Clean tracked worktrees confirmed (no uncommitted changes)
- [ ] Git LFS/pointer state recorded
- [ ] Supplied documentation hashes recorded
- [ ] Repository trees, artifact hashes, sizes, and dependency manifests recorded
- [ ] Repository B integration branch `integration/sih-round2-selective-merge` created
- [ ] Repository A marked as read-only evidence source
- [ ] Pre-merge reproduction logs saved under `logs/`

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

## Risk Register

| Risk | Mitigation |
|---|---|
| Repository SHAs have moved since audit | Record new SHA, timestamp, reason; re-run inventory |
| LFS pointers mistaken for binaries | `file` command verification; never deploy pointer text |
| Workspace contamination | Always start from `rm -rf` or fresh directory |
| Missing documentation | Hash all supplied docs; identify gaps before proceeding |

---

**Next:** [Phase 0 — Freeze and Inventory](02_phase0_freeze_and_inventory.md) (only after ALL exit criteria pass)
