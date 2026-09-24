# Implementation Plan — Phase 2: Base Selection and Branch Controls

## Objective

Establish Repository B as the sole application destination and enforce branch controls that prevent a monolithic merge, duplicate trees, or uncontrolled imports.

## Entry Criteria

- [ ] Phase 1 complete: claim register built, evidence classes assigned
- [ ] All public claims have owners and dispositions
- [ ] No undocumented claim awaiting classification

## What Gets Imported from Repository A (Allowlist Only)

These are the ONLY patterns that may be ported from A — **no application trees, no pointer binaries:**

| Pattern | Source File(s) |
|---|---|
| Safe model-unavailable behavior | `v3_model_adapter.py`, `predict.py` |
| UTC and issue-time contract | `time_contract.py` |
| Certification-scope boundaries | `certification_policy.py` |
| Provider/fixture disclosure | Provider adapters, disagreement tests |
| Revision-store semantics | `revision_store.py`, `revision_service.py` |
| Replay invariants | `replay_harness.py`, `golden_replay_matrix.py` |
| Selected safety and release tests | `test_day34*`, `test_day35*`, `test_day37*`, `test_day38*`, `test_scientific_certification*` |

## What Stays in Repository B (Destination)

| Component | Path |
|---|---|
| Backend application | `backend/app/` |
| Versioned API routes | `backend/app/api/` |
| Frontend application | `frontend/src/` |
| Model services & registries | `backend/app/builder2/` |
| CI/CD workflow | `.github/workflows/deploy.yml` |
| Test suites | `backend/tests/`, frontend tests |
| Dependencies | `requirements.txt`, `pyproject.toml`, lock files |

## Implementation Steps

### Step 2.1 — Create Protected Integration Branch

```bash
cd "$WORKSPACE/repos/repo_b"
git switch integration/sih-round2-selective-merge

# Verify branch is clean
git status --short
git log --oneline -5
```

### Step 2.2 — Define Branch Protection Rules

Create `.github/branch-protection.md` documenting:
- Integration branch requires pull requests
- Required checks must pass before merge
- No force pushes
- No direct commits

### Step 2.3 — Define Canonical Destination Directories

Create `manifests/canonical_directory_map.md`:

```text
backend/
├── app/
│   ├── api/            ← Versioned routes (SINGULAR)
│   ├── builder2/       ← Model adapters, specialists (SINGULAR)
│   ├── core/           ← Core policies, contracts (SINGULAR)
│   ├── data/           ← Data stores (SINGULAR)
│   ├── safety/         ← OOD, abstention (SINGULAR)
│   └── services/       ← Business services (SINGULAR)
├── tests/              ← All backend tests (SINGULAR)
frontend/
├── src/                ← Frontend source (SINGULAR)
models/
├── v3/                 ← V3 model artifacts (SINGULAR)
scripts/                ← Utility scripts (SINGULAR)
manifests/              ← Asset ledgers, claim registers
docs/                   ← Documentation
data/                   ← Data files (SINGULAR)
```

### Step 2.4 — Define No-Duplicate Policy

**RULE:** There must be exactly ONE of each:

| Component | Allowed Count | Current Violation Risk |
|---|---|---|
| Backend application tree | 1 | A has Builder-2, Parinidhi duplicates |
| Frontend application tree | 1 | A has Frontend-Original duplicate |
| Model registry | 1 | — |
| Release manifest location | 1 | — |
| Route-to-model authority | 1 | — |
| Dependency lock file (Python) | 1 | — |
| Dependency lock file (Node) | 1 | — |

### Step 2.5 — Create Import Allowlist

Create `manifests/import_allowlist.csv`:

| Source | Path | Destination | Action | Owner | Gate |
|---|---|---|---|---|---|
| A | `time_contract.py` | `backend/app/core/` | adapt | — | Phase 4 |
| A | `certification_policy.py` | `backend/app/core/` | adapt | — | Phase 4 |
| A | `ood_policy.py` | `backend/app/core/` | adapt | — | Phase 4 |
| A | `v3_model_adapter.py` (safe-fail patterns) | merge into B's adapter | adapt | — | Phase 4 |
| A | `predict.py` (safe-fail patterns) | merge into B's routes | adapt | — | Phase 4 |
| A | `revision_service.py` | `backend/app/services/` | adapt | — | Phase 5 |
| A | Selected test files | `backend/tests/` | port | — | Phase 4 |

### Step 2.6 — Create Import Denylist

Create `manifests/import_denylist.csv`:

| Source | Path/Pattern | Reason |
|---|---|---|
| A | `models/v3/*.joblib` | Git LFS pointers, not deployable |
| A | `Builder-2/` | Duplicate application tree |
| A | `Parinidhi/` | Duplicate application tree |
| A | `Frontend-Original/` | Duplicate application tree |
| A | `Overview/` | Historical tree |
| A | Unverified specialist metrics | No independent validation |
| B | Specialist JSON metrics as "reproduced" | Not independently re-run |
| B | Synthetic outputs labeled as "live" | Scientific misrepresentation |
| B | Stale certification claims | Contradicted by evidence |

### Step 2.7 — Define Module Ownership

Create `manifests/code_owners.md`:

| Module | Owner | Responsibility |
|---|---|---|
| Model registry (`models/v3/`) | — | Artifact integrity, hash verification |
| Safety (`backend/app/safety/`, `core/`) | — | OOD, abstention, certification boundaries |
| Data history (`backend/app/data/`) | — | Revision store, replay, truth sealing |
| API (`backend/app/api/`) | — | Routes, schemas, versioning |
| UI (`frontend/src/`) | — | Provenance banners, trust states |
| Tests (`backend/tests/`) | — | Test migration, coverage |
| Documentation (`docs/`) | — | Claim accuracy, evidence labels |

### Step 2.8 — Establish Single Dependency Path

- One `requirements.txt` or `pyproject.toml` for Python
- One `package.json` / `package-lock.json` for Node
- No competing virtual environments in production

### Step 2.9 — Add Merge-Check Script

Create `scripts/check_import_compliance.py` that:
- Rejects files copied outside the allowlist without owner + validation plan
- Checks for duplicate application trees
- Verifies no denied files are present

## Outputs Checklist

- [ ] Protected integration branch created and verified
- [ ] Canonical directory map documented
- [ ] Import allowlist with per-file gates
- [ ] Import denylist with reasons
- [ ] Module ownership map (CODEOWNERS-style)
- [ ] Single dependency lock established
- [ ] Merge-check script operational

## Failure Conditions — Immediate Stop If:

| Condition | Why It Matters |
|---|---|
| A second app tree is introduced | Violates single-destination rule |
| A's historical trees copied without disposition | Uncontrolled merge |
| Model-serving code in multiple competing paths | Ambiguous model authority |
| Branch can deploy without required checks | Governance bypass |

## Gate P0-2

**The destination must have:**
- ONE backend
- ONE frontend
- ONE model registry
- ONE release manifest location
- ONE route-to-model authority

## Compulsory Gate Test

```bash
set -euo pipefail
test "$(git branch --show-current)" = "integration/sih-round2-selective-merge"
test -d backend/app
test -d frontend/src
! find . -maxdepth 2 -type d \( -name 'Builder-2' -o -name 'Parinidhi' -o -name 'Frontend-Original' -o -name 'Overview' \) -print | grep -q .
find . -path '*/models/v3/*' -type f | sort
```

**Pass condition:** Repository B is the only application destination, no historical application tree has been imported, and the integration branch is cleanly identified.

---

**Previous:** [Phase 1 — Truth Alignment](03_phase1_truth_alignment.md)  
**Next:** [Phase 3 — Artifact Repair](05_phase3_artifact_repair.md)
