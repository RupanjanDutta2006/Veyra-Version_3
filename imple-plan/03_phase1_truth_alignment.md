# Implementation Plan — Phase 1: Truth Alignment and Claim Register

## Objective

Make documentation, source code, artifacts, tests, and runtime claims agree across both repositories before moving any code. Build a master claim register that classifies every public scientific claim by evidence class.

## Entry Criteria

- [ ] Phase 0 complete: inventory frozen, SHAs verified, asset ledger created
- [ ] Both repos have clean worktrees with recorded hashes
- [ ] No integration edits have been made yet

## Inputs

### From Repository A
| File/Module | Purpose |
|---|---|
| `backend/app/core/certification_policy.py` | Certification scope/wording |
| `backend/app/core/time_contract.py` | UTC and issue-time contract |
| `backend/app/core/ood_policy.py` | OOD behavior policy |
| Provider adapter and disagreement tests | Provider safety patterns |
| `Audits/VEYRA_*` material | Previous audit evidence |
| Current README and integration contracts | Public-facing claims |

### From Repository B
| File/Module | Purpose |
|---|---|
| `ARCHITECTURE.md` | Architecture claims |
| `REPRODUCIBILITY_PACKAGE.md` | Reproducibility claims |
| `docs/*` | All documentation |
| `.round2-roadmap/*` | Roadmap claims |
| `round2-report/*` | Report claims |
| `backend/app/builder2/*specialist.py` modules | Specialist claims |
| Specialist JSON metrics and certification manifests | Metric claims |
| `cross_system_transfer_engine.py` and digital-twin material | Cross-system claims |

## Implementation Steps

### Step 1.1 — Create the Claim Register Structure

Create `manifests/claim_register.csv` with columns:

| Column | Description |
|---|---|
| `claim_id` | Unique identifier (e.g., CLM-001) |
| `claim` | The exact claim text |
| `source_file` | File where claim originates |
| `code_path` | Implementing code path (if any) |
| `artifact_path` | Supporting artifact (if any) |
| `test_command` | Test that validates claim (if any) |
| `runtime_observation` | Runtime evidence (if any) |
| `evidence_class` | Classification (see below) |
| `current_status` | Current state |
| `owner` | Person/team responsible |
| `correction` | Required action |
| `documentation_disposition` | retain / rewrite / archive / reject |

### Step 1.2 — Classify Every Major Claim

Use these evidence classes:

| Evidence Class | Definition |
|---|---|
| `REPRODUCED` | Tests run, artifacts loaded, outputs verified now |
| `SUPPORTED_BY_ARTIFACT` | Frozen artifact chain exists but not re-run |
| `SUPPORTED_BY_CODE_ONLY` | Code exists but no independent validation |
| `SUPPORTED_BY_TEST_FIXTURE_ONLY` | Tests pass but only against fixtures, not real data |
| `DOCUMENTATION_ONLY` | Claim exists only in docs/README |
| `CONTRADICTED` | Evidence conflicts with the claim |
| `UNVERIFIED` | Cannot determine truth from available evidence |

### Step 1.3 — Audit Certification Language

**Action:** Remove or qualify ALL broad `CERTIFIED` language where independent scientific evidence is absent.

Key claims to audit:
- "6 Certified Meteorological Hazard Specialists" → classify each specialist's actual evidence
- Specific Brier/ECE values per hazard → verify against actual rerun data
- Conditional conformal coverage / ≥90% coverage claims → check for real held-out data
- +24h to +96h advance warning → check for real event evaluation
- NCMRWF/IMD/DWR/INSAT ingestion → check for real paired data
- Cross-system transferability → check for real multi-source validation
- Digital-twin scientific conclusions → label as synthetic/fixture

### Step 1.4 — Label Specialist Formulas

For each of B's six specialists:
- `precipitation_specialist.py` → Is it a trained model or deterministic formula?
- `cyclone_specialist.py` → Same question
- `monsoon_specialist.py` → Same question
- `western_disturbance_specialist.py` → Same question
- `heatwave_specialist.py` → Same question
- (severe wind) → Does it exist?

**Label each as:** `trained_model`, `formula_baseline`, `deterministic_formula`, or `missing`

### Step 1.5 — Label Synthetic vs Historical Data

- Digital-twin synthetic progression → Label as `SYNTHETIC` or `FIXTURE`
- Fallback/risk-map/cached paths → Label in both API and UI terms
- Any deterministic risk-map output → Cannot appear as live observation

### Step 1.6 — Separate Semantic Concepts

Ensure these are **separate fields and code paths** (not conflated):
1. Calibrated P(BUST)
2. Hazard probability (cyclone, heavy-rain, heatwave occurrence)
3. Continuous forecast error
4. Prediction interval coverage
5. Ensemble-member dispersion
6. Provider disagreement
7. OOD/novelty detection
8. Confidence heuristic
9. Scientific certification

### Step 1.7 — Audit Data Source Claims

Mark as `FUTURE` or `DOCUMENTATION_ONLY` unless ALL of these exist:
- Paired data
- Metadata
- Permission/authorization
- Replay evidence

Systems requiring this check:
- NCMRWF
- NEPS
- IMD
- DWR
- INSAT
- Cross-system statements

### Step 1.8 — Correct Test Count Claims

- Record actual discovered test count vs. claimed test count
- Never equate total test count with "500-test certification"
- Keep discovered counts separate from the named 500-test identity

### Step 1.9 — Add Documentation Drift Disposition

For every document, assign one of:

| Disposition | Meaning |
|---|---|
| `RETAIN` | Accurate, keep as-is |
| `REWRITE` | Contains truth but needs correction |
| `ARCHIVE` | Historical value only, move to archive |
| `REJECT` | Contradicted or misleading, remove |

## Outputs Checklist

- [ ] Master claim register (`manifests/claim_register.csv`)
- [ ] Stale/contradicted documentation list
- [ ] Corrected README and release-language draft
- [ ] Evidence-class labels for ALL public claims
- [ ] UI/API provenance wording specification
- [ ] Specialist classification (trained vs formula vs missing)
- [ ] Synthetic/fixture label inventory

## Failure Conditions — Immediate Stop If:

| Condition | Why It Matters |
|---|---|
| Unsupported certification remains in production-facing text | Misleads users/judges |
| Synthetic outputs can be interpreted as historical/live | Scientific dishonesty |
| Hazard probability exposed as `P(BUST)` without separate target | Semantic conflation |
| A metric labeled "reproduced" without rerun or valid chain | False evidence |

## Gate P0-1

**Every public scientific claim must map to an evidence class and a current owner.** No undocumented claim can be promoted in later phases.

## Compulsory Gate Test

```bash
set -euo pipefail
test -s manifests/claim_register.csv
python3 scripts/validate_claim_register.py \
  --input manifests/claim_register.csv \
  --required-classes REPRODUCED,SUPPORTED_BY_ARTIFACT,SUPPORTED_BY_CODE_ONLY,SUPPORTED_BY_TEST_FIXTURE_ONLY,DOCUMENTATION_ONLY,CONTRADICTED,UNVERIFIED
! grep -RInE '(^|[^A-Za-z])(CERTIFIED|live historical|NCMRWF validated)' docs README.md 2>/dev/null | \
  grep -vE 'DOCUMENTATION_ONLY|UNVERIFIED|experimental' || true
```

**Pass condition:** Every major claim has an evidence class, source path, owner, and correction. Unsupported certification and live-science wording is removed or explicitly qualified.

---

**Previous:** [Phase 0 — Freeze and Inventory](02_phase0_freeze_and_inventory.md)  
**Next:** [Phase 2 — Base Selection](04_phase2_base_selection.md)
