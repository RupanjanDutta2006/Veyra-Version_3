import os
import csv
import json

WORKSPACE = os.path.abspath(".")
MANIFESTS = os.path.join(WORKSPACE, "manifests")

ALLOWED_CLASSES = [
    "REPRODUCED",
    "SUPPORTED_BY_ARTIFACT",
    "SUPPORTED_BY_CODE_ONLY",
    "SUPPORTED_BY_TEST_FIXTURE_ONLY",
    "DOCUMENTATION_ONLY",
    "CONTRADICTED",
    "UNVERIFIED"
]

CLAIMS = [
    {
        "claim_id": "CLM-001",
        "claim": "V3 LightGBM Challenger Model (1,046,844 bytes, SHA256 00a8410746...) is loadable binary artifact",
        "source_file": "repos/repo_b/models/v3/lightgbm_v3_challenger.joblib",
        "code_path": "backend/app/builder2/v3_model_adapter.py",
        "artifact_path": "models/v3/lightgbm_v3_challenger.joblib",
        "test_command": "python -c \"import joblib; m = joblib.load('repos/repo_b/models/v3/lightgbm_v3_challenger.joblib'); print(type(m))\"",
        "runtime_observation": "Model loads successfully into memory; scikit-learn/lightgbm Booster estimator verified in Repo B",
        "evidence_class": "REPRODUCED",
        "current_status": "Active canonical binary in Repo B; in Repo A Git LFS pointer text on un-smudged checkouts",
        "owner": "Model Custodian",
        "correction": "Ensure Repo B binary remains canonical; quarantine Repo A pointer file",
        "documentation_disposition": "RETAIN"
    },
    {
        "claim_id": "CLM-002",
        "claim": "V3 Isotonic Probability Calibrator (2,791 bytes, SHA256 9f448606ce...) is loadable calibrator",
        "source_file": "repos/repo_b/models/v3/probability_calibrator_v3.joblib",
        "code_path": "backend/app/builder2/v3_model_adapter.py",
        "artifact_path": "models/v3/probability_calibrator_v3.joblib",
        "test_command": "python -c \"import joblib; c = joblib.load('repos/repo_b/models/v3/probability_calibrator_v3.joblib'); print(type(c))\"",
        "runtime_observation": "Calibrator loads successfully into memory; IsotonicRegression object confirmed",
        "evidence_class": "REPRODUCED",
        "current_status": "Active canonical calibrator in Repo B",
        "owner": "Model Custodian",
        "correction": "Retain as canonical calibrator in release manifest",
        "documentation_disposition": "RETAIN"
    },
    {
        "claim_id": "CLM-003",
        "claim": "V3 Feature Names schema (50 features, SHA256 22687bf2a6...) matches artifact_manifest expected hash b65d642301...",
        "source_file": "repos/repo_b/artifact_manifest.json",
        "code_path": "scripts/verify_artifacts.py",
        "artifact_path": "models/v3/feature_names.json",
        "test_command": "python repos/repo_b/scripts/verify_artifacts.py",
        "runtime_observation": "Verification exits 1: Expected b65d642301... but calculated 22687bf2a6...",
        "evidence_class": "CONTRADICTED",
        "current_status": "Known checksum mismatch in Repo B",
        "owner": "Release Engineer",
        "correction": "Repair feature-manifest hash chain in Phase 3 after verifying 50-feature order matches model expectation",
        "documentation_disposition": "REWRITE"
    },
    {
        "claim_id": "CLM-004",
        "claim": "V3 Operational Serving Decision Threshold is 0.060 (not legacy Day-4 0.280)",
        "source_file": "repos/repo_b/backend/app/builder2/v3_model_adapter.py",
        "code_path": "backend/app/builder2/v3_model_adapter.py",
        "artifact_path": "models/v3/v3_evaluation_manifest.json",
        "test_command": "grep -rn '0.06' repos/repo_b/backend/app/builder2/",
        "runtime_observation": "V3 decision threshold is 0.060; Day 4 baseline was 0.280",
        "evidence_class": "SUPPORTED_BY_CODE_ONLY",
        "current_status": "Multiple hardcoded thresholds exist across different test files",
        "owner": "Serving Engineer",
        "correction": "Centralize V3 serving threshold to exactly 0.060 in release manifest and model adapter",
        "documentation_disposition": "REWRITE"
    },
    {
        "claim_id": "CLM-005",
        "claim": "6 Certified Meteorological Hazard Specialists exist and are empirically validated on Indian events",
        "source_file": "repos/repo_b/README.md",
        "code_path": "backend/app/builder2/*specialist.py",
        "artifact_path": "None (no trained model weights exist)",
        "test_command": "python -c \"import inspect, backend.app.builder2.precipitation_specialist\"",
        "runtime_observation": "Specialists are deterministic physics heuristics/formulas (e.g. CAPE/rh thresholds), not ML models, and no empirical dataset exists",
        "evidence_class": "CONTRADICTED",
        "current_status": "Unvalidated scientific claim in README",
        "owner": "Science Governance Lead",
        "correction": "Quarantine as experimental heuristic modules; re-label as 'Prototype Hazard Reliability Heuristics'",
        "documentation_disposition": "REWRITE"
    },
    {
        "claim_id": "CLM-006",
        "claim": "Conditional Conformal Coverage guarantees >=90% empirical coverage across all regimes",
        "source_file": "repos/repo_b/README.md",
        "code_path": "backend/app/builder2/conditional_calibration_engine.py",
        "artifact_path": "data/hazard_calibration_registry.json",
        "test_command": "pytest backend/tests/test_conditional_calibration.py",
        "runtime_observation": "Tested against synthetic random/fixture numbers only, no real held-out spatial meteorological test set",
        "evidence_class": "SUPPORTED_BY_TEST_FIXTURE_ONLY",
        "current_status": "Fixture-supported only",
        "owner": "Uncertainty Lead",
        "correction": "Label conformal coverage as theoretical prototype demonstrated on fixtures; remove unconditional guarantee",
        "documentation_disposition": "REWRITE"
    },
    {
        "claim_id": "CLM-007",
        "claim": "+24h to +96h Advance Warning Lead Time for forecast bust detection",
        "source_file": "repos/repo_b/README.md",
        "code_path": "backend/app/services/horizon_reliability_service.py",
        "artifact_path": "data/horizon_metrics.json",
        "test_command": "None",
        "runtime_observation": "No historical storm/bust event timeline evaluation exists",
        "evidence_class": "DOCUMENTATION_ONLY",
        "current_status": "Theoretical claim",
        "owner": "Meteorologist",
        "correction": "Demote to 'Architected multi-horizon tracking (+24h to +96h) capability; empirical lead time pending live trials'",
        "documentation_disposition": "REWRITE"
    },
    {
        "claim_id": "CLM-008",
        "claim": "Live ingestion and validation against NCMRWF, NEPS, IMD, DWR, and INSAT",
        "source_file": "repos/repo_b/README.md",
        "code_path": "backend/app/services/ncmrwf_service.py (mock/stub)",
        "artifact_path": "None",
        "test_command": "None",
        "runtime_observation": "Only Open-Meteo public API is actually connected; national data integration is mock/stub",
        "evidence_class": "DOCUMENTATION_ONLY",
        "current_status": "Mocked/planned integration",
        "owner": "Data Ingestion Lead",
        "correction": "Explicitly state: 'Public-proxy demonstration via Open-Meteo; NCMRWF/IMD/DWR interfaces architected as target adapters'",
        "documentation_disposition": "REWRITE"
    },
    {
        "claim_id": "CLM-009",
        "claim": "Cross-System Transferability validated between global NWP models (ECMWF, GFS, ICON)",
        "source_file": "repos/repo_b/cross_system_transfer_engine.py",
        "code_path": "cross_system_transfer_engine.py",
        "artifact_path": "data/cross_system_transfer_matrix.json",
        "test_command": "python evaluate_cross_system.py",
        "runtime_observation": "Evaluates mock correlation numbers without paired raw forecast archives",
        "evidence_class": "SUPPORTED_BY_TEST_FIXTURE_ONLY",
        "current_status": "Experimental heuristic engine",
        "owner": "Research Lead",
        "correction": "Keep in experimental registry; do not claim validated transferability",
        "documentation_disposition": "REWRITE"
    },
    {
        "claim_id": "CLM-010",
        "claim": "Digital Twin Replay evaluates real historical bust cycles",
        "source_file": "repos/repo_b/replay_digital_twin.py",
        "code_path": "replay_digital_twin.py",
        "artifact_path": "data/digital_twin_scenarios.json",
        "test_command": "python replay_digital_twin.py",
        "runtime_observation": "Script synthesizes scenario progression in-memory with deterministic math; not physical atmospheric simulation",
        "evidence_class": "SUPPORTED_BY_TEST_FIXTURE_ONLY",
        "current_status": "Synthetic simulation demonstration",
        "owner": "Simulation Lead",
        "correction": "Label replay scenarios clearly as SYNTHETIC DEMONSTRATION in UI and logs",
        "documentation_disposition": "REWRITE"
    },
    {
        "claim_id": "CLM-011",
        "claim": "816 Passing Tests in CI/CD pipeline",
        "source_file": "repos/repo_b/README.md",
        "code_path": "backend/tests/",
        "artifact_path": "None",
        "test_command": "pytest backend/tests -q",
        "runtime_observation": "758 passed backend tests in Repo B + 58 frontend vitest tests = 816 combined test executions",
        "evidence_class": "REPRODUCED",
        "current_status": "Confirmed 758 backend + 58 frontend test executions",
        "owner": "QA Lead",
        "correction": "Retain fact: 758 backend pytest + 58 frontend vitest tests pass; clarify that software test count is distinct from scientific validation",
        "documentation_disposition": "RETAIN"
    },
    {
        "claim_id": "CLM-012",
        "claim": "Dual Provider Cross-Provider Disagreement Engine",
        "source_file": "repos/repo_a/backend/app/services/disagreement_service.py",
        "code_path": "backend/app/services/disagreement_service.py",
        "artifact_path": "tests/fixtures/mock_provider_b.json",
        "test_command": "pytest test_day38_cross_provider_disagreement.py",
        "runtime_observation": "Provider A fetches live Open-Meteo; Provider B uses mock fixture. Repo A tested the contract, Repo B lacked dual provider adapter",
        "evidence_class": "SUPPORTED_BY_TEST_FIXTURE_ONLY",
        "current_status": "Contract tested in Repo A, needs porting to Repo B with fixture label",
        "owner": "Integration Architect",
        "correction": "Port provider disagreement engine from Repo A to Repo B with clear 'MOCK_SECONDARY_PROVIDER' label",
        "documentation_disposition": "REWRITE"
    },
    {
        "claim_id": "CLM-013",
        "claim": "Issue-Time UTC Contract and Sealed Episode Truth prevents future information leakage",
        "source_file": "repos/repo_a/backend/app/core/time_contract.py",
        "code_path": "backend/app/core/time_contract.py",
        "artifact_path": "None",
        "test_command": "pytest backend/tests/test_v3_time_contract.py",
        "runtime_observation": "Strict ISO-8601 UTC validation rejects naive timestamps and enforces immutable issue times",
        "evidence_class": "REPRODUCED",
        "current_status": "Present in Repo A, missing in parts of Repo B",
        "owner": "Safety Architect",
        "correction": "Port time_contract.py and tests from Repo A into Repo B in Phase 4",
        "documentation_disposition": "RETAIN"
    },
    {
        "claim_id": "CLM-014",
        "claim": "OOD / Novelty Abstention Policy returns uncalibrated status or refuses prediction on extreme OOD",
        "source_file": "repos/repo_a/backend/app/core/ood_policy.py",
        "code_path": "backend/app/core/ood_policy.py",
        "artifact_path": "None",
        "test_command": "pytest backend/tests/test_v3_ood_policy.py",
        "runtime_observation": "Repo A defines explicit abstention and null probability semantics; Repo B has separate OOD detector",
        "evidence_class": "REPRODUCED",
        "current_status": "To be consolidated in Phase 4",
        "owner": "Safety Architect",
        "correction": "Graft Repo A's honest abstention contract into Repo B's OOD detector in Phase 4",
        "documentation_disposition": "RETAIN"
    }
]

def main():
    print("=== STARTING PHASE 1: TRUTH ALIGNMENT AND CLAIM REGISTER ===")

    # 1. Write manifests/claim_register.csv
    csv_path = os.path.join(MANIFESTS, "claim_register.csv")
    fieldnames = [
        "claim_id", "claim", "source_file", "code_path", "artifact_path",
        "test_command", "runtime_observation", "evidence_class",
        "current_status", "owner", "correction", "documentation_disposition"
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(CLAIMS)
    print(f"Generated {len(CLAIMS)} claims in {csv_path}")

    # 2. Write manifests/specialist_classification.csv
    spec_path = os.path.join(MANIFESTS, "specialist_classification.csv")
    specialists = [
        {"specialist": "precipitation_specialist.py", "classification": "deterministic_formula", "trained_model_exists": "NO", "dataset": "None (CAPE/RH heuristic rules)", "status": "EXPERIMENTAL_PROTOTYPE"},
        {"specialist": "cyclone_specialist.py", "classification": "deterministic_formula", "trained_model_exists": "NO", "dataset": "None (Pressure drop/vorticity formula)", "status": "EXPERIMENTAL_PROTOTYPE"},
        {"specialist": "monsoon_specialist.py", "classification": "deterministic_formula", "trained_model_exists": "NO", "dataset": "None (Low-level jet/shear rule)", "status": "EXPERIMENTAL_PROTOTYPE"},
        {"specialist": "western_disturbance_specialist.py", "classification": "deterministic_formula", "trained_model_exists": "NO", "dataset": "None (Subtropical jet/trough rule)", "status": "EXPERIMENTAL_PROTOTYPE"},
        {"specialist": "heatwave_specialist.py", "classification": "deterministic_formula", "trained_model_exists": "NO", "dataset": "None (Temperature percentile threshold)", "status": "EXPERIMENTAL_PROTOTYPE"},
        {"specialist": "severe_wind_specialist.py", "classification": "missing", "trained_model_exists": "NO", "dataset": "None", "status": "PLANNED_FUTURE"}
    ]
    with open(spec_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["specialist", "classification", "trained_model_exists", "dataset", "status"])
        writer.writeheader()
        writer.writerows(specialists)
    print(f"Generated specialist classification in {spec_path}")

    # 3. Write manifests/documentation_disposition.csv
    doc_disp_path = os.path.join(MANIFESTS, "documentation_disposition.csv")
    doc_dispositions = [
        {"doc_path": "README.md", "disposition": "REWRITE", "action_required": "Remove '6 Certified Specialists' claim; update test count breakdown; note Open-Meteo proxy data; specify V3 0.060 threshold"},
        {"doc_path": "ARCHITECTURE.md", "disposition": "REWRITE", "action_required": "Align architecture diagrams with actual single active destination and experimental specialist boundaries"},
        {"doc_path": "REPRODUCIBILITY_PACKAGE.md", "disposition": "REWRITE", "action_required": "Add clear distinction between software test reproduction and empirical scientific validation"},
        {"doc_path": "BUILDER_1_BUILDER_2_INTEGRATION_CONTRACT.md", "disposition": "RETAIN", "action_required": "Keep as historical evidence reference with audited SHA link"},
        {"doc_path": "BUILDER_2_HANDOFF.md", "disposition": "RETAIN", "action_required": "Keep as reference document with evidence labels"},
        {"doc_path": "Parinidhi/README.md", "disposition": "ARCHIVE", "action_required": "Mark as historical unmerged tree"},
        {"doc_path": "Builder-2/README.md", "disposition": "ARCHIVE", "action_required": "Mark as historical unmerged tree"},
        {"doc_path": "Frontend-Original/README.md", "disposition": "REJECT", "action_required": "Quarantined duplicate tree"}
    ]
    with open(doc_disp_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["doc_path", "disposition", "action_required"])
        writer.writeheader()
        writer.writerows(doc_dispositions)
    print(f"Generated documentation dispositions in {doc_disp_path}")

    # 4. Write manifests/corrected_scientific_language.md
    guide_path = os.path.join(MANIFESTS, "corrected_scientific_language.md")
    content = """# Veyra Scientific Communication & Certification Boundary Guide

## 1. Truth in Terminology Standards

To ensure scientific honesty and maintain alignment with the evidence hierarchy:

| Forbidden / Misleading Term | Approved Honest Term | Scientific Reason |
|---|---|---|
| "6 Certified Meteorological Hazard Specialists" | "6 Prototype Hazard Reliability Heuristic Engines" | The specialist modules use deterministic formulas/rules, not trained, independently calibrated machine learning models. |
| "Certified P(Bust) Predictor" | "Calibrated Forecast Bust Sentinel (V3 LightGBM Incumbent)" | Certification requires independent operational body authority. Veyra provides well-calibrated statistical uncertainty. |
| "Live NCMRWF / NEPS / IMD Operational Feed" | "Demonstration Feed via Open-Meteo Public NWP (National Adaptor Architecture Ready)" | Only Open-Meteo live API is connected. National agency feeds are architected as stub/adapter endpoints. |
| "Digital Twin Atmospheric Simulation" | "Interactive Synthetic Progression Demonstration" | The replay scripts deterministically simulate scenario metrics for UI evaluation, not physical atmospheric physics. |
| "Empirical Guarantee of >=90% Conformal Coverage" | "Prototype Conformal Calibration Layer (Tested on Fixtures)" | True coverage guarantees require extensive out-of-distribution real-world validation. |
| "Dual Live Ensemble Disagreement" | "Cross-Provider Disagreement Engine (Provider A Live, Provider B Fixture)" | Only Provider A is live; Provider B runs against test fixtures. |

## 2. Separate Semantic Concepts Standard

Code and UI must never conflate the following 9 distinct concepts:
1. `calibrated_p_bust`: Calibrated probability (0.0 to 1.0) that issued forecast error exceeds critical threshold.
2. `hazard_probability`: Probability of severe meteorological event occurrence (e.g. rain > 65mm).
3. `continuous_error_estimate`: Predicted magnitude of parameter deviation (e.g. +/- 4.2 C).
4. `conformal_interval`: Validated coverage interval at 1 - alpha significance.
5. `ensemble_dispersion`: Spread among NWP ensemble members.
6. `provider_disagreement`: Quantitative divergence between independent forecast models (e.g. ECMWF vs GFS).
7. `ood_novelty_score`: Distance of current atmospheric state from model training manifold.
8. `confidence_heuristic`: Composite operational heuristic score.
9. `certification_status`: Explicit declaration of whether model meets formal boundary standards.
"""
    with open(guide_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Generated scientific language guide in {guide_path}")

    print("=== PHASE 1 EXECUTION COMPLETE ===")

if __name__ == "__main__":
    main()
