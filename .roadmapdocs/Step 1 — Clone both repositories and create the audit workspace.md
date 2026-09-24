# Step 1 — Clone both repositories and create the audit workspace

This is the first operational step. Do not begin by copying modules, merging branches, installing dependencies into an untracked directory, or editing either upstream repository. Clone both repositories into separate directories, preserve the upstream state, and perform all integration work in a new destination branch derived from Repository B.

## 1.1 Create the workspace

Run these commands from a clean shell with Git, Python, Node.js, and package-management tools available:

```bash
set -euo pipefail

export WORKSPACE="$HOME/veyra-sih-round2"
rm -rf "$WORKSPACE"
mkdir -p "$WORKSPACE"/{repos,artifacts,logs,docs,manifests,builds}
cd "$WORKSPACE"
```

Do not use a path that already contains uncommitted work. If an existing workspace must be retained, use a new directory instead of deleting it.

## 1.2 Clone Repository A and Repository B separately

```bash
cd "$WORKSPACE/repos"

git clone https://github.com/RupanjanDutta2006/Veyra-Know-When-Forecasts-May-Fail repo_a
git clone https://github.com/adishxm/Veyra-Know-When-Forecasts-May-Fail-VERSION-2 repo_b

git -C repo_a remote -v
git -C repo_b remote -v
git -C repo_a branch --show-current
git -C repo_b branch --show-current
git -C repo_a rev-parse HEAD
git -C repo_b rev-parse HEAD
```

At the audited state, the expected branches and SHAs are:

```text
Repository A: main / b9f52d3eeec8676e06b1879f05b404605e2501be
Repository B: main / 82eded8194151e37fb9b3eecf273010dc62d7b29
```

If either remote has moved, do not silently substitute the new code. Record the new SHA, timestamp, and reason, then repeat the artifact, test, and source inventory.

## 1.3 Preserve the cloned states

```bash
cd "$WORKSPACE/repos"
git -C repo_a status --short
git -C repo_b status --short
git -C repo_a log -1 --format='%H%n%cI%n%s' > "$WORKSPACE/manifests/repo_a_head.txt"
git -C repo_b log -1 --format='%H%n%cI%n%s' > "$WORKSPACE/manifests/repo_b_head.txt"
git -C repo_a tag -a audit-repo-a-b9f52d3 -m 'Frozen SIH Round-2 audit state' b9f52d3eeec8676e06b1879f05b404605e2501be
git -C repo_b tag -a audit-repo-b-82eded8 -m 'Frozen SIH Round-2 audit state' 82eded8194151e37fb9b3eecf273010dc62d7b29
```

If tagging is not permitted, create annotated archive metadata under `$WORKSPACE/manifests`. Never rewrite either upstream `main` branch.

## 1.4 Check Git LFS and record artifact state

Repository A’s V3 paths were observed as Git LFS pointer text rather than loadable binaries. Record that state before any attempt to merge:

```bash
git lfs version || true
git -C "$WORKSPACE/repos/repo_a" lfs ls-files || true
file "$WORKSPACE/repos/repo_a/models/v3/lightgbm_v3_challenger.joblib" || true
file "$WORKSPACE/repos/repo_a/models/v3/probability_calibrator_v3.joblib" || true
sha256sum "$WORKSPACE/repos/repo_a/models/v3/lightgbm_v3_challenger.joblib" || true
sha256sum "$WORKSPACE/repos/repo_a/models/v3/probability_calibrator_v3.joblib" || true
```

Do not run `git lfs pull` and treat the result as the same evidence without recording payload source, object ID, size, SHA256, and authorization. A recovered payload is a new artifact requiring provenance and revalidation.

## 1.5 Create the documentation and evidence bundle

Place the supplied archive, authoritative `MASTER PROMPT.txt`, research pack, 500-test suite, blueprint, main specification, and previous comparison report under `$WORKSPACE/docs`. Record their hashes:

```bash
find "$WORKSPACE/docs" -type f -print0 | sort -z | xargs -0 sha256sum > "$WORKSPACE/manifests/supplied_docs.sha256"
```

Do not double-count duplicate copies. Select one authoritative copy per document and record duplicate paths in a duplicate-disposition ledger.

## 1.6 Inventory both repositories before installing or editing

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

Record backend, frontend, model, data, scripts, tests, docs, CI, deployment, and release paths separately. Installation-generated files must not be mixed with the clean-checkout inventory.

## 1.7 Create the destination integration branch

Only after both repositories are recorded:

```bash
cd "$WORKSPACE/repos/repo_b"
git switch -c integration/sih-round2-selective-merge
git status --short
```

Repository A remains a read-only evidence source. Repository B is the only application destination. Every imported file must be recorded in the asset ledger with source SHA, destination path, action, owner, and validation gate.

## 1.8 Install dependencies in isolated environments

Do not install dependencies globally or modify either clean clone. Use separate environments for initial reproduction:

```bash
python3 -m venv "$WORKSPACE/builds/repo_a_venv"
python3 -m venv "$WORKSPACE/builds/repo_b_venv"
python3 -m venv "$WORKSPACE/builds/integration_venv"
source "$WORKSPACE/builds/integration_venv/bin/activate"
python -m pip install --upgrade pip
```

Install only from declared requirements/lock files after the clean inventory. Record Python, Node, npm/pnpm, LightGBM, scikit-learn, and model-serialization versions.

## 1.9 Reproduce before merge

Before copying a file from either repository, run the available artifact verification, test collection, bounded tests, frontend build, startup smoke, and release/replay commands in the original checkout. Save stdout, stderr, exit code, warnings, and runtime under `$WORKSPACE/logs`. This prevents a merged system from hiding a pre-existing failure.

## Step 1 exit criteria

- [ ] Both repositories cloned separately.
- [ ] Default branches and SHAs recorded.
- [ ] Clean tracked worktrees confirmed.
- [ ] Git LFS/pointer state recorded.
- [ ] Supplied documentation hashes recorded.
- [ ] Repository trees, artifact hashes, sizes, and dependency manifests recorded.
- [ ] Repository B integration branch created.
- [ ] Repository A marked read-only evidence source.
- [ ] Pre-merge reproduction logs saved.

Only after every item passes should Phase 0 begin.

## Compulsory test for Step 1 — inventory and freeze

Run from the workspace root after the inventory is generated:

```bash
set -euo pipefail
test "$(git -C repos/repo_a status --porcelain)" = ""
test "$(git -C repos/repo_b status --porcelain)" = ""
git -C repos/repo_a rev-parse HEAD | grep -q '^b9f52d3eeec8676e06b1879f05b404605e2501be$'
git -C repos/repo_b rev-parse HEAD | grep -q '^82eded8194151e37fb9b3eecf273010dc62d7b29$'
test -s manifests/repo_a_artifact_hashes.sha256
test -s manifests/repo_b_artifact_hashes.sha256
```

**Pass condition:** both clean-checkout inventories, SHAs, and artifact-hash manifests exist and match the frozen evidence.
