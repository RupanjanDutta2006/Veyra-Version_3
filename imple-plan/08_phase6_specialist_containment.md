# Implementation Plan — Phase 6: Experimental Module Containment and Scientific Promotion Boundary

## Objective

Keep Repository B's broad specialist architecture without allowing unvalidated modules to enter the incumbent production path. Establish clear boundaries between experimental, formula-baseline, and production-promoted code.

## Entry Criteria

- [ ] Phase 5 complete: durable revision store operational, replay separation working
- [ ] G9 (revision durability) and G11 (replay separation) gates pass
- [ ] Historical vs synthetic modes are visibly separate

## The Specialist Landscape in Repository B

| Specialist Module | Path | Current Nature |
|---|---|---|
| Precipitation | `backend/app/builder2/precipitation_specialist.py` | Deterministic formula |
| Cyclone | `backend/app/builder2/cyclone_specialist.py` | Deterministic formula |
| Monsoon/LPS | `backend/app/builder2/monsoon_specialist.py` | Deterministic formula |
| Western Disturbance | `backend/app/builder2/western_disturbance_specialist.py` | Deterministic formula |
| Heatwave | `backend/app/builder2/heatwave_specialist.py` | Deterministic formula |
| Spatial Reliability | `spatial_reliability_engine.py` | Experimental engine |
| Compound Hazard | `compound_hazard_engine.py` | Experimental engine |
| Common Mode | `common_mode_detector.py` | Experimental detector |
| Cross-System Transfer | `cross_system_transfer_engine.py` | Experimental engine |
| Evidence Graph | `evidence_graph_engine.py` | Explanation interface |
| Explainer | `explainer.py` | Explanation interface |

**KEY INSIGHT:** All six hazard specialists are **deterministic formula-based** — they use fixed coefficients and thresholds, NOT trained ML models. They are NOT "certified" and must not be called trained/certified.

## Implementation Steps

### Step 6.1 — Create Specialist Registry

Create `backend/app/builder2/specialist_registry.py`:

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class SpecialistStatus(str, Enum):
    EXPERIMENTAL = "experimental"      # Not validated for production
    FORMULA_BASELINE = "formula_baseline"  # Deterministic formula, not trained
    CANDIDATE = "candidate"            # Under active evaluation
    PROMOTED = "promoted"              # Passed all promotion gates
    QUARANTINED = "quarantined"        # Evidence issues found

@dataclass
class SpecialistRegistration:
    name: str
    module_path: str
    status: SpecialistStatus
    feature_flag: str
    hazard_type: str
    is_formula: bool                   # True if deterministic, not trained
    has_trained_artifact: bool         # True if has .joblib/.pkl model
    evidence_package_path: Optional[str]
    promotion_gate_status: Optional[str]
    reviewer_signoff: Optional[str]

REGISTRY = {
    "precipitation": SpecialistRegistration(
        name="Precipitation Reliability",
        module_path="backend/app/builder2/precipitation_specialist.py",
        status=SpecialistStatus.FORMULA_BASELINE,
        feature_flag="ENABLE_PRECIPITATION_SPECIALIST",
        hazard_type="precipitation",
        is_formula=True,
        has_trained_artifact=False,
        evidence_package_path=None,
        promotion_gate_status=None,
        reviewer_signoff=None,
    ),
    # ... repeat for all specialists
}
```

### Step 6.2 — Put Specialists Behind Feature Flags

```python
# backend/app/core/feature_flags.py
FEATURE_FLAGS = {
    "ENABLE_PRECIPITATION_SPECIALIST": False,  # Experimental
    "ENABLE_CYCLONE_SPECIALIST": False,
    "ENABLE_MONSOON_SPECIALIST": False,
    "ENABLE_WESTERN_DISTURBANCE_SPECIALIST": False,
    "ENABLE_HEATWAVE_SPECIALIST": False,
    "ENABLE_SPATIAL_ENGINE": False,
    "ENABLE_COMPOUND_HAZARD": False,
    "ENABLE_COMMON_MODE": False,
    "ENABLE_CROSS_SYSTEM": False,
}
```

**Rule:** Specialists cannot affect production responses unless their feature flag is explicitly enabled AND they have passed promotion gates.

### Step 6.3 — Separate Formula from Trained Outputs

```python
class SpecialistOutput:
    value: float
    output_type: OutputType  # FORMULA | TRAINED_MODEL | ENSEMBLE
    coefficients_source: str  # Where coefficients came from
    is_calibrated: bool
    calibrator_artifact: Optional[str]
    confidence_note: str  # "deterministic formula" or "trained on X data"
```

### Step 6.4 — Add Provenance Fields

Every specialist output must include:

| Field | Description |
|---|---|
| `coefficients_source` | Where thresholds/coefficients originate |
| `input_data_source` | What data was used |
| `model_artifact_id` | If trained, which artifact (or `None` for formulas) |
| `training_data_split` | If trained, what split was used |
| `evaluation_manifest` | Link to evaluation results |

### Step 6.5 — Add Per-Hazard Target Definitions

For each hazard specialist, document:

```json
{
  "hazard": "precipitation",
  "target_definition": "Forecast bust for heavy rainfall (>64.5mm/24h)",
  "data_splits": {
    "train": "NOT_TRAINED (formula_baseline)",
    "validation": "NOT_APPLICABLE",
    "out_of_time": "NOT_APPLICABLE"
  },
  "seeds": "NOT_APPLICABLE",
  "artifact_id": "NONE (deterministic formula)",
  "evaluation_manifest": "PENDING"
}
```

### Step 6.6 — Define Promotion Gates

A specialist is promoted from `experimental` to `promoted` ONLY after passing ALL:

| Gate | Metric | Threshold |
|---|---|---|
| Calibration | Brier Score | < V3 incumbent |
| Calibration | BSS (Brier Skill Score) | > 0 |
| Calibration | ECE (Expected Calibration Error) | < 0.05 |
| Calibration | Calibration slope | 0.8–1.2 |
| Calibration | Calibration intercept | < 0.02 |
| Discrimination | PR-AUC | > V3 incumbent |
| Timeliness | Warning lead time | Documented |
| Uncertainty | Interval coverage | ≥ 90% |
| Robustness | Bootstrap uncertainty | Documented CI |
| Safety | OOD performance | Documented |
| Generalization | Out-of-time performance | Documented |
| Independence | Independent reviewer | Sign-off required |

### Step 6.7 — Separate Hazard from Bust Targets

**Rule:** Hazard occurrence and forecast-bust targets MUST be separate:

```python
# WRONG: Conflating hazard with bust
cyclone_probability = 0.85  # This is hazard occurrence, NOT bust probability

# RIGHT: Separate targets
hazard_occurrence_probability = 0.85  # P(cyclone exists)
bust_probability_given_hazard = 0.32  # P(forecast fails | cyclone exists)
```

### Step 6.8 — Quarantine Unsupported Claims

Move to quarantine list (do NOT delete, just isolate):
- Specialist JSON metrics not independently re-run
- Cross-system transfer values without paired data
- Conformal/coverage figures without held-out validation
- Warning-lead numbers without real event evaluation
- Common-mode claims based only on fixtures

### Step 6.9 — Keep Advanced Paths Experimental

All of these remain `EXPERIMENTAL`:
- Spatial reliability engine
- Compound hazard engine
- Common mode detector
- Cross-system transfer engine

### Step 6.10 — Non-Causal Explanation Contract

```python
class ExplanationPolicy:
    """
    Evidence-graph and explanation outputs must use non-causal wording
    unless causal evidence exists.
    """
    ALLOWED_WORDING = [
        "associated with",
        "correlated with",
        "observed pattern",
        "co-occurring with",
    ]
    FORBIDDEN_WORDING = [
        "caused by",
        "due to",
        "because of",
        "leads to",  # unless causal evidence exists
    ]
```

### Step 6.11 — Reject Severe Wind Certification

Severe wind specialist does NOT exist as an independent package. Any claims must be marked `MISSING` or `FUTURE_BY_DESIGN`.

### Step 6.12 — Add Independent Reviewer Gate

No specialist can be promoted without:
1. Complete evidence package submitted
2. Independent reviewer assigned
3. Reviewer re-runs evaluation
4. Reviewer signs off on results
5. Sign-off recorded in specialist registry

## Outputs Checklist

- [ ] Experimental module registry (`specialist_registry.py`)
- [ ] Formula-baseline labels for all six specialists
- [ ] Feature flags for all experimental modules
- [ ] Per-hazard promotion template
- [ ] Specialist evidence package schema
- [ ] Quarantined unsupported claims list
- [ ] Non-causal explanation contract
- [ ] Independent reviewer gate process

## Failure Conditions — Immediate Stop If:

| Condition | Why |
|---|---|
| Any formula called "trained" or "certified" | Misrepresentation |
| Specialist changes incumbent output without promotion gates | V3 integrity violation |
| Hazard probability surfaced as `P(BUST)` | Semantic conflation |
| JSON metric treated as "reproduced" without rerun | False evidence |
| Cross-system/common-mode claims rely only on fixtures | Unvalidated |

## Gate G8

**No specialist enters the production path until an independent package contains:**
- Source data provenance
- Issue-time split
- Target definition
- Feature schema
- Trained artifact (or formula documentation)
- Calibrator if used
- Model hash
- Evaluation script
- Raw outputs
- Bootstrap/OOT/OOD results
- Reviewer sign-off

## Compulsory Gate Test

```bash
set -euo pipefail
pytest -q backend/tests/test_specialist_registry.py \
  backend/tests/test_experimental_feature_flags.py \
  backend/tests/test_claim_boundaries.py
python scripts/check_production_specialists.py --fail-on-unvalidated-promotion
```

**Pass condition:** Every deterministic specialist is labeled experimental or formula baseline, no unsupported `CERTIFIED` promotion is possible, and specialist outputs cannot silently replace the V3 incumbent.

---

**Previous:** [Phase 5 — Revision & Replay](07_phase5_revision_replay.md)  
**Next:** [Phase 7 — CI, Test, Release](09_phase7_ci_test_release.md)
