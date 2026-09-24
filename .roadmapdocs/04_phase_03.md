# Phase 3 — Frozen incumbent artifact repair

## Objective

Repair Repository B’s feature-contract integrity while preserving the loadable V3 model and isotonic calibrator.

## Inputs from Repository A

- Strict feature-order checks in `v3_feature_pipeline.py`.
- Model-unavailable and no-silent-fallback behavior from `v3_model_adapter.py` and `predict.py`.
- Expected production hashes from the frozen contract.
- Artifact/release test patterns.

## Inputs from Repository B

- `models/v3/lightgbm_v3_challenger.joblib`.
- `models/v3/probability_calibrator_v3.joblib`.
- `models/v3/feature_names.json`.
- `artifact_manifest.json`.
- `training_manifest.json`.
- `v3_evaluation_manifest.json`.
- `v3_comprehensive_evaluation.json`.
- `scripts/verify_artifacts.py`.
- `backend/app/builder2/v3_model_adapter.py`.
- `models/day4/*` and `models/baseline_logistic_v1*` for explicit baseline comparison only.

## Known incumbent contract

| Item | Required value |
|---|---|
| V3 model | `models/v3/lightgbm_v3_challenger.joblib` |
| Model SHA256 | `00a8410746f4a0eecbf7e76aaa0565143fc948d0e06aea65e7bcc4ce28a1c660` |
| Calibrator | `models/v3/probability_calibrator_v3.joblib` |
| Calibrator SHA256 | `9f448606ce4338ded92f238a551b3a9d8e6d2cb5902e8bc687bce5f5850af531` |
| Feature count | 50 |
| Calibrator type | `IsotonicRegression` |

## Step-by-step work

1. Determine whether the committed `feature_names.json` or its declared hash is authoritative.
2. Do not alter the model or calibrator to make a hash pass.
3. If the feature file is canonical, regenerate the manifest from that exact file and record the decision.
4. If the manifest is canonical, restore the exact feature file from a verified source and record provenance.
5. Pin the compatible scikit-learn and LightGBM environment.
6. Load the model and calibrator in a clean clone.
7. Verify model type, calibrator type, feature count, feature order, threshold, model ID, and fallback policy.
8. Create one release manifest binding all of those values.
9. Consolidate V3 threshold `0.060` and legacy Day-4 threshold `0.280` into an explicit model-version map; do not silently choose one.
10. Make `scripts/verify_artifacts.py` exit 0.
11. Add a clean-clone artifact test.
12. Add a golden-input prediction parity test before and after all safety grafts.
13. Verify that missing or corrupt artifacts produce a safe abstention and never an unannounced model substitution.

## Outputs

- One authoritative V3 release manifest.
- Verified hashes and environment lock.
- Route-to-model/threshold/fallback map.
- Clean-clone verifier result with exit code 0.
- Golden V3 output fixture and parity test.
- Artifact provenance record.

## Failure conditions

- Feature hash remains inconsistent.
- Model or calibrator is changed without an approved provenance record.
- Multiple thresholds or fallback paths remain undocumented.
- Silent fallback changes the calibrated output.
- Clean-clone load fails.

## Gates G1–G3

- **G1 Artifact integrity:** all hashes, types, feature order, environment, ID, threshold, and fallback match.
- **G2 Incumbent parity:** golden calibrated V3 outputs remain identical within declared tolerance.
- **G3 Model authority:** exactly one authoritative model path per route.

No safety grafting or specialist integration proceeds if G1–G3 fail.

## Compulsory test for Phase 3 — incumbent artifact integrity

Run the repository verifier and explicit model/calibrator checks:

```bash
set -euo pipefail
python scripts/verify_artifacts.py
python - <<'PY'
from pathlib import Path
import joblib
model = Path('models/v3/lightgbm_v3_challenger.joblib')
cal = Path('models/v3/probability_calibrator_v3.joblib')
assert model.exists() and cal.exists()
joblib.load(cal)
print('model/calibrator paths present and calibrator deserializes')
PY
```

**Pass condition:** verifier exits 0, hashes match one authoritative manifest, the calibrator loads as `IsotonicRegression`, the feature list has 50 entries, and route/model/threshold/fallback authority is singular.
