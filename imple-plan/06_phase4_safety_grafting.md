# Implementation Plan — Phase 4: Selective Safety Grafting

## Objective

Port only Repository A patterns that improve operational honesty and failure safety into Repository B's codebase, without changing the V3 incumbent model output.

## Entry Criteria

- [ ] Phase 3 complete: G1–G3 gates pass
- [ ] V3 artifact integrity verified (hashes, types, feature order)
- [ ] Golden V3 output fixture created (`artifacts/golden_v3_before.json`)
- [ ] Release manifest is authoritative and singular

## What Gets Ported (And What Doesn't)

### Port These Safety Patterns from A → B

| Pattern | Source in A | Destination in B | Purpose |
|---|---|---|---|
| UTC/issue-time contract | `backend/app/core/time_contract.py` | `backend/app/core/time_contract.py` | Prevent future-information leakage |
| Safe model-unavailable | `v3_model_adapter.py`, `predict.py` | Merge into B's adapter/routes | Abstain safely when model missing |
| Certification scope policy | `certification_policy.py` | `backend/app/core/certification_policy.py` | Wording/scope, NOT proof |
| OOD policy | `ood_policy.py` | `backend/app/core/ood_policy.py` | Separate diagnostic vs active OOD |
| Provider disclosure | Provider adapters | B's response schema | Show provider identity |
| Revision semantics | `revision_service.py` | `backend/app/services/` | After storage contract agreed |
| Safety tests | `test_day34*`, `test_day35*`, `test_day37*`, `test_day38*`, `test_scientific_certification*`, `test_v3_*` | `backend/tests/` | Port test intent |

### Do NOT Port

- A's application trees (`Builder-2`, `Parinidhi`, `Frontend-Original`)
- A's pointer model/calibrator binaries
- A's frontend components wholesale
- Any module that duplicates existing B functionality

## Implementation Steps

### Step 4.1 — Port UTC and Issue-Time Contract

Adapt A's `time_contract.py` into B's canonical data contract:

- All features at issue time `t0` must use only information available at or before `t0`
- Prohibited: future observations, future reanalysis, verifying imagery, future errors, labels, post-valid-time data
- Add issue-time validation function
- Add leakage detection tests

**Verification:** Write tests that fail if future data enters the feature vector.

### Step 4.2 — Port Safe Model-Unavailable Behavior

Modify B's `v3_model_adapter.py` to add:
- If model file is missing → return `UNAVAILABLE` status, NOT silent fallback
- If model is corrupted → return `UNAVAILABLE` status
- If calibrator is missing → return `UNAVAILABLE` status
- Never substitute a different model without explicit announcement

**Critical rule:** B's SUCCESSFUL V3 output must not change.

### Step 4.3 — Define Explicit Response States

Add to B's prediction response schema:

```python
class PredictionStatus(str, Enum):
    READY = "ready"           # Normal prediction available
    ABSTAIN = "abstain"       # Model declines (e.g., low confidence)
    OOD = "ood"               # Out-of-distribution input detected
    UNAVAILABLE = "unavailable"  # Model/data not available
    LIVE = "live"             # Using live data
    CACHED = "cached"         # Using cached data
    FIXTURE = "fixture"       # Using test fixture data
    FALLBACK = "fallback"     # Using fallback model/data
    SYNTHETIC = "synthetic"   # Synthetic/simulated data
```

### Step 4.4 — Port Certification Policy (Scope Only)

Port A's `certification_policy.py` as a **scope and wording policy**, not as proof of certification:

```python
class CertificationPolicy:
    """
    Controls what wording the system may use about its scientific status.
    This is a SCOPE BOUNDARY, not proof of certification.
    """
    CERTIFIED_SCOPE = {
        "stations": 25,
        "variables": 3,
        "max_horizon_hours": 240,
    }
    
    FORBIDDEN_WORDING = [
        "certified" (unless evidence class is REPRODUCED),
        "validated" (unless paired data exists),
        "live historical" (unless immutable replay data exists),
    ]
```

### Step 4.5 — Consolidate OOD Behavior

Make diagnostic OOD and active abstention **separate fields and code paths**:

```python
class OODResult:
    diagnostic_score: float        # Informational OOD signal
    is_diagnostic_only: bool       # True if not used for abstention
    active_abstention: bool        # True if model should abstain
    abstention_threshold: float    # Gate that triggers abstention
    abstention_reason: str         # Why abstention was triggered
```

### Step 4.6 — Port Provider Identity and Fixture Disclosure

Add to B's response schema:

```python
class ProvenanceInfo:
    provider_id: str               # Which data provider
    data_mode: DataMode            # live/cached/fixture/fallback/synthetic
    issue_utc: datetime            # When prediction was issued
    valid_utc: datetime            # When prediction is valid for
    fixture_disclosure: Optional[str]  # If fixture, explain what
```

### Step 4.7 — Port Revision Semantics

Only after agreeing on canonical storage contract (Phase 5 dependency):
- Define revision record schema
- Define idempotency keys
- Define truth-sealing rules

### Step 4.8 — Port A Tests into B Style

For each test being ported:

| A Test | B Destination | Test Intent |
|---|---|---|
| `test_day34_time_contract_revision_store.py` | `backend/tests/test_time_contract.py` | UTC safety, revision integrity |
| `test_day35_independent_replay_release_manifest.py` | `backend/tests/test_replay_release.py` | Replay independence, manifest integrity |
| `test_day37_provider_adapters.py` | `backend/tests/test_provider_adapters.py` | Provider identity, disclosure |
| `test_day38_cross_provider_disagreement.py` | `backend/tests/test_provider_disagreement.py` | Disagreement detection |
| `test_scientific_certification.py` | `backend/tests/test_certification_scope.py` | Certification boundaries |
| `test_v3_*` relevant tests | `backend/tests/test_v3_safety.py` | V3 safety behaviors |

**Rule:** Maintain test intent and source traceability. Add comments linking back to A source.

### Step 4.9 — Add API Schema-Diff Tests

Create tests that verify the API schema remains backward-compatible:
- Compare OpenAPI spec before/after safety changes
- Ensure no field removals
- Ensure no semantic changes to existing fields

### Step 4.10 — Run V3 Golden Parity After Every Change

```bash
python scripts/compare_golden_v3_outputs.py \
  --baseline artifacts/golden_v3_before.json \
  --candidate artifacts/golden_v3_after.json
```

**This must run after EVERY safety change.** If golden output differs → revert the change.

### Step 4.11 — Add Failure-Path Tests

Create tests for:
- Missing model file → safe abstention
- Corrupted model file → safe abstention
- Missing provider → explicit error
- Stale data (past cache TTL) → appropriate status
- Invalid timestamp → reject with error

## Outputs Checklist

- [ ] B-native safety modules (time contract, certification policy, OOD policy)
- [ ] Unified trust/provenance response schema
- [ ] Migrated safety and disclosure tests (with source traceability)
- [ ] Explicit OOD/abstention contract (diagnostic vs active separated)
- [ ] Certification wording and UI policy
- [ ] API schema-diff tests
- [ ] Failure-path tests for all edge cases
- [ ] V3 golden parity confirmed after all changes

## Failure Conditions — Immediate Stop If:

| Condition | Why |
|---|---|
| Probability fields change semantics | Breaks downstream consumers |
| Provider identity or UTC identity dropped | Loses provenance |
| Diagnostic OOD becomes active abstention without documented gate | Undocumented behavior change |
| Safety changes alter golden V3 results | Incumbent corrupted |
| A fixture is exposed as live | Scientific dishonesty |

## Gates

- [ ] V3 parity remains green
- [ ] Issue-time leakage tests pass
- [ ] Missing-model behavior abstains safely
- [ ] API schemas preserve separate bust, hazard, OOD, uncertainty, and provenance fields

## Compulsory Gate Test

```bash
set -euo pipefail
pytest -q backend/tests/test_v3_* backend/tests/test_scientific_certification.py
pytest -q backend/tests/test_day34_time_contract_revision_store.py \
  backend/tests/test_day37_provider_adapters.py \
  backend/tests/test_day38_cross_provider_disagreement.py
python scripts/compare_golden_v3_outputs.py \
  --baseline artifacts/golden_v3_before.json \
  --candidate artifacts/golden_v3_after.json
```

**Pass condition:** Tests pass, missing-model behavior abstains safely, UTC/provider/provenance fields remain present, and golden calibrated V3 outputs remain within declared tolerance.

---

**Previous:** [Phase 3 — Artifact Repair](05_phase3_artifact_repair.md)  
**Next:** [Phase 5 — Revision & Replay](07_phase5_revision_replay.md)
