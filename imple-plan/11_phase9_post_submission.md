# Implementation Plan — Phase 9: Post-Submission Empirical Specialist Program

## Objective

Conduct scientific specialist promotion work AFTER the safe software base is submitted, without destabilizing the V3 incumbent. This is the long-term scientific program for upgrading formula baselines into trained, validated specialists.

## Entry Criteria

- [ ] Phase 8 complete: SIH Round-2 candidate submitted
- [ ] V3 incumbent is stable and passing all gates
- [ ] All specialists are behind feature flags and labeled correctly
- [ ] Specialist registry is operational

## What Repository A Contributes

**No specialist artifacts accepted as equivalent.** A contributes only:
- Safety patterns
- Disclosure patterns
- Evaluation-boundary patterns

## What Repository B Provides

| Input | Purpose |
|---|---|
| Six specialist formula baselines | Starting points for empirical work |
| Spatial/compound/common-mode/transfer prototypes | Experimental code to build on |
| Hazard target/event JSON | Target definitions |
| Specialist manifests | Current configuration |
| Calibration registry | Calibration infrastructure |
| Evaluation and replay scripts | Evaluation tools |

## Implementation Steps (Per Hazard Specialist)

### Step 9.1 — Define Actual Data Sources Per Hazard

For each hazard, document:

| Hazard | Forecast Source | Reference Truth | Issue Time | Valid Time | Data Horizon |
|---|---|---|---|---|---|
| Precipitation | Open-Meteo (public proxy) | ERA5/station obs | T+0h | T+24h to T+240h | 2020–present |
| Cyclone | Open-Meteo (public proxy) | IBTrACS/IMD | T+0h | T+24h to T+96h | Historical events |
| Monsoon/LPS | Open-Meteo (public proxy) | ERA5/IMD | T+0h | T+24h to T+240h | Monsoon seasons |
| Western Disturbance | Open-Meteo (public proxy) | ERA5/station obs | T+0h | T+24h to T+120h | Winter seasons |
| Heatwave | Open-Meteo (public proxy) | ERA5/station obs | T+0h | T+24h to T+120h | Summer seasons |

### Step 9.2 — Build Leakage-Safe Splits

For each hazard:

```python
class LeakageSafeSplit:
    train_start: datetime
    train_end: datetime
    validation_start: datetime
    validation_end: datetime
    out_of_time_start: datetime
    out_of_time_end: datetime
    event_holdout: List[str]    # Specific events held out
    ood_test_regions: List[str]  # Regions not in training
    
    def validate_no_leakage(self):
        """Ensure no temporal overlap between splits."""
        assert self.train_end < self.validation_start
        assert self.validation_end < self.out_of_time_start
```

### Step 9.3 — Produce Real Trained Artifacts

For each specialist candidate:

```python
# Training pipeline
def train_specialist(hazard: str, split: LeakageSafeSplit):
    # 1. Load training data (issue-time safe)
    train_data = load_data(split.train_start, split.train_end, hazard)
    
    # 2. Extract features (no future information)
    features = extract_issue_time_features(train_data)
    
    # 3. Train model
    model = train_model(features, target='bust_label')
    
    # 4. Calibrate
    cal_data = load_data(split.validation_start, split.validation_end, hazard)
    calibrator = calibrate_model(model, cal_data)
    
    # 5. Save artifacts with hashes
    save_artifact(model, f'models/specialists/{hazard}_challenger.joblib')
    save_artifact(calibrator, f'models/specialists/{hazard}_calibrator.joblib')
    
    # 6. Record provenance
    return TrainingManifest(
        model_hash=hash_file(model_path),
        calibrator_hash=hash_file(cal_path),
        feature_schema=features.columns.tolist(),
        training_rows=len(train_data),
        seed=42,
    )
```

### Step 9.4 — Compare Against V3 and Baseline Ladder

```python
BASELINE_LADDER = [
    "climatology",           # Always-predict-base-rate
    "persistence",           # Predict yesterday's bust rate
    "logistic_v1",           # Baseline logistic (from day4)
    "v3_incumbent",          # Current LightGBM V3
    "specialist_candidate",  # New trained specialist
]

for baseline in BASELINE_LADDER:
    evaluate(baseline, out_of_time_data, metrics=ALL_METRICS)
```

### Step 9.5 — Reproduce All Required Metrics

For each specialist candidate, compute and report:

| Metric | Description |
|---|---|
| Brier Score | Calibration + discrimination |
| BSS (Brier Skill Score) | Improvement over climatology |
| ECE | Expected Calibration Error |
| Calibration slope | Reliability diagram slope |
| Calibration intercept | Reliability diagram intercept |
| PR-AUC | Precision-Recall area under curve |
| FAR | False Alarm Rate |
| Detection (POD) | Probability of Detection |
| Warning lead time | Hours of advance notice |
| Interval coverage | Prediction interval coverage |
| Bootstrap uncertainty | 2000-iteration bootstrap CIs |

### Step 9.6 — Evaluate by Stratification

```python
STRATIFICATIONS = [
    "hazard_type",    # Per-hazard breakdown
    "horizon",        # 24h, 48h, 72h, 96h, etc.
    "geography",      # Per-station or per-region
    "season",         # Monsoon, winter, summer, etc.
    "regime",         # Active, break, onset, withdrawal
    "provider",       # Which data provider
]

for strat in STRATIFICATIONS:
    evaluate_stratified(specialist, out_of_time_data, stratify_by=strat)
```

### Step 9.7 — Evaluate Abstention and Risk-Coverage

```python
def evaluate_abstention(specialist, held_out_shifts):
    """
    Evaluate specialist's abstention behavior under distribution shifts.
    """
    for shift in held_out_shifts:
        shifted_data = apply_distribution_shift(out_of_time_data, shift)
        predictions = specialist.predict(shifted_data)
        
        abstention_rate = sum(p.status == 'abstain' for p in predictions) / len(predictions)
        accuracy_when_not_abstaining = compute_accuracy(
            [p for p in predictions if p.status != 'abstain']
        )
        
        print(f"Shift: {shift.name}")
        print(f"  Abstention rate: {abstention_rate:.3f}")
        print(f"  Accuracy (non-abstaining): {accuracy_when_not_abstaining:.3f}")
```

### Step 9.8 — Re-Run Spatial, Compound, Common-Mode, Cross-System

Evaluate with **independent truth** (not self-referential):

```bash
python scripts/evaluate_spatial_propagation.py --truth-source independent
python scripts/evaluate_cross_system.py --truth-source independent
```

### Step 9.9 — Test Historical Replay Without Synthetic

```bash
python scripts/replay_historical.py \
  --mode historical \
  --reject-synthetic \
  --fixtures artifacts/immutable_forecast_truth_fixture
```

### Step 9.10 — Promotion Decision

For each specialist, the decision is binary:

**PROMOTE if ALL of these hold:**
- Brier Score < V3 incumbent (for this hazard)
- BSS > 0
- ECE < 0.05
- Calibration slope in [0.8, 1.2]
- Bootstrap CIs don't overlap with V3 at α=0.05
- OOT performance is consistent
- OOD detection works
- Independent reviewer signed off

**RETAIN V3 if ANY of these hold:**
- No incremental value over V3
- Calibration failure
- Coverage failure
- No reproducible artifact chain
- Future leakage detected
- No paired truth data

### Step 9.11 — Record Failure/Success

```python
# manifests/specialist_promotion_decisions.json
{
    "precipitation": {
        "decision": "RETAIN_V3",  # or "PROMOTE_SPECIALIST"
        "reason": "Formula baseline, no trained artifact",
        "brier_vs_v3": "N/A - formula comparison",
        "reviewer": null,
        "date": "2026-09-21"
    },
    # ... for each hazard
}
```

## Outputs Checklist

- [ ] Per-hazard empirical evidence package
- [ ] Reproducible model/calibrator artifacts (if trained)
- [ ] OOT/OOD/uncertainty reports
- [ ] Promotion or rejection decision for each specialist
- [ ] Updated claim register
- [ ] Baseline ladder comparison
- [ ] Stratified evaluation reports

## Failure Conditions — Immediate Stop If:

| Condition | Why |
|---|---|
| Future leakage detected | Invalid evaluation |
| No paired truth or permission | Cannot validate |
| No incremental value over V3 | No reason to promote |
| Calibration or coverage failure | Not reliable enough |
| No reproducible artifact chain | Not reproducible |

## Promotion Gate

A specialist is promoted ONLY after:
1. Independent reproduction of all metrics
2. Explicit acceptance by incumbent/challenger gate
3. Software integration alone CANNOT promote a specialist

## Compulsory Gate Test

```bash
set -euo pipefail
python scripts/evaluate_specialist.py \
  --hazard precipitation --split out_of_time \
  --require-issue-time-lineage --bootstrap 2000
python scripts/evaluate_specialist.py \
  --hazard cyclone --split out_of_time \
  --require-issue-time-lineage --bootstrap 2000
python scripts/evaluate_specialist.py \
  --hazard monsoon_lps --split out_of_time \
  --require-issue-time-lineage --bootstrap 2000
python scripts/evaluate_specialist.py \
  --hazard western_disturbance --split out_of_time \
  --require-issue-time-lineage --bootstrap 2000
python scripts/evaluate_specialist.py \
  --hazard heatwave --split out_of_time \
  --require-issue-time-lineage --bootstrap 2000
```

**Pass condition:** Each promoted specialist has a reproducible trained artifact, target and feature contract, leakage-safe split, calibration/uncertainty/OOD report, and independent review. If any candidate fails, retain V3 and keep the specialist experimental.

---

**Previous:** [Phase 8 — Submission Readiness](10_phase8_submission_readiness.md)  
**Next:** [Asset Collection Plan](12_asset_collection_plan.md)
