"""Specialist Registry and Scientific Promotion Boundary for Veyra Round 2.

Establishes strict architectural boundaries separating:
1. Production incumbent path (V3 frozen benchmark LightGBM + calibrator)
2. Formula-based baselines (deterministic heuristics with fixed coefficients)
3. Experimental engines (spatial, compound, common-mode, cross-system transfer)
4. Quarantined or missing modules (e.g. severe wind)

INVARIANTS (Gate G8):
- No formula is ever represented as a trained or certified ML model.
- P(Hazard) is strictly separated from P(Bust | Hazard).
- No specialist output can silently enter or alter the production V3 response
  unless promoted through an independent evidence package and signed off by a reviewer.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import re

from backend.app.core.feature_flags import is_feature_enabled


class SpecialistStatus(str, Enum):
    EXPERIMENTAL = "experimental"              # Not validated for production
    FORMULA_BASELINE = "formula_baseline"      # Deterministic formula, not trained ML
    CANDIDATE = "candidate"                    # Under active scientific peer review
    PROMOTED = "promoted"                      # Passed all 12 Gate G8 promotion criteria
    QUARANTINED = "quarantined"                # Missing evidence, conflicting metrics, or isolated


class SpecialistOutputType(str, Enum):
    FORMULA = "formula"
    TRAINED_MODEL = "trained_model"
    ENSEMBLE = "ensemble"


@dataclass
class SpecialistRegistration:
    name: str
    module_path: str
    status: SpecialistStatus
    feature_flag: str
    hazard_type: str
    is_formula: bool
    has_trained_artifact: bool
    evidence_package_path: Optional[str] = None
    promotion_gate_status: Optional[str] = None
    reviewer_signoff: Optional[str] = None
    target_definition: Optional[str] = None
    data_split_info: Optional[str] = None
    model_sha256: Optional[str] = None
    target_manifest_path: Optional[str] = None
    bust_formula: Optional[str] = None
    evidence_tier: str = "FORMULA_BASELINE"


@dataclass
class SpecialistOutput:
    specialist_name: str
    value: float
    output_type: SpecialistOutputType
    coefficients_source: str
    is_calibrated: bool
    calibrator_artifact: Optional[str]
    confidence_note: str
    # Strict separation: Hazard occurrence vs Forecast bust given hazard
    hazard_occurrence_probability: Optional[float] = None
    bust_probability_given_hazard: Optional[float] = None
    provenance_metadata: Dict[str, Any] = field(default_factory=dict)


class ExplanationPolicy:
    """Enforces non-causal observational wording for evidence graph and explanations.
    
    Prevents assertions of causation when only correlation/association exists.
    """
    ALLOWED_TERMS = [
        "associated with",
        "correlated with",
        "observed pattern",
        "co-occurring with",
        "consistent with",
        "indicative of",
    ]

    FORBIDDEN_TERMS = [
        r"\bcaused by\b",
        r"\bdue to\b",
        r"\bbecause of\b",
        r"\bleads to\b",
        r"\btriggers\b",
    ]

    @classmethod
    def audit_explanation_text(cls, text: str) -> Tuple[bool, List[str]]:
        """Audit explanation text for forbidden causal claims.
        
        Returns (is_compliant, list_of_violations).
        """
        violations = []
        for pattern in cls.FORBIDDEN_TERMS:
            if re.search(pattern, text, re.IGNORECASE):
                violations.append(f"Forbidden causal phrasing found: '{pattern}'")
        return (len(violations) == 0, violations)


SPECIALIST_REGISTRY: Dict[str, SpecialistRegistration] = {
    "precipitation": SpecialistRegistration(
        name="Precipitation Reliability Specialist",
        module_path="backend/app/builder2/precipitation_specialist.py",
        status=SpecialistStatus.FORMULA_BASELINE,
        feature_flag="ENABLE_PRECIPITATION_SPECIALIST",
        hazard_type="precipitation",
        is_formula=True,
        has_trained_artifact=False,
        evidence_package_path="docs/science-evidence/pilot_evidence_package_precipitation.md",
        promotion_gate_status="UNPROMOTED_FORMULA",
        reviewer_signoff=None,
        target_definition="Forecast bust for heavy rainfall (>= 64.5mm/24h) and amount error",
        data_split_info="NOT_TRAINED (deterministic heuristic rules)",
        model_sha256=None,
        target_manifest_path="data/precipitation_target_manifest.json",
        bust_formula="|F_24h - O_24h| > 25.0 mm OR (F_24h >= 64.5 AND O_24h < 64.5) OR (F_24h < 64.5 AND O_24h >= 64.5)",
        evidence_tier="FORMULA_BASELINE",
    ),
    "cyclone": SpecialistRegistration(
        name="Cyclone Reliability Specialist",
        module_path="backend/app/builder2/cyclone_specialist.py",
        status=SpecialistStatus.FORMULA_BASELINE,
        feature_flag="ENABLE_CYCLONE_SPECIALIST",
        hazard_type="cyclone",
        is_formula=True,
        has_trained_artifact=False,
        evidence_package_path=None,
        promotion_gate_status="UNPROMOTED_FORMULA",
        reviewer_signoff=None,
        target_definition="NWP track displacement (>150km) and intensity bust (>20 knots)",
        data_split_info="NOT_TRAINED (deterministic heuristic rules)",
        model_sha256=None,
        target_manifest_path="data/cyclone_target_manifest.json",
        bust_formula="|Track_Error_48h| > 120km OR |Intensity_Error_48h| > 15 knots",
        evidence_tier="FORMULA_BASELINE",
    ),
    "monsoon": SpecialistRegistration(
        name="Monsoon/LPS Reliability Specialist",
        module_path="backend/app/builder2/monsoon_specialist.py",
        status=SpecialistStatus.FORMULA_BASELINE,
        feature_flag="ENABLE_MONSOON_SPECIALIST",
        hazard_type="monsoon_lps",
        is_formula=True,
        has_trained_artifact=False,
        evidence_package_path=None,
        promotion_gate_status="UNPROMOTED_FORMULA",
        reviewer_signoff=None,
        target_definition="Low pressure system track displacement and moisture flux error",
        data_split_info="NOT_TRAINED (deterministic heuristic rules)",
        model_sha256=None,
        target_manifest_path="data/monsoon_target_manifest.json",
        bust_formula="Low pressure center displacement > 150km OR Swath error > 50mm",
        evidence_tier="FORMULA_BASELINE",
    ),
    "western_disturbance": SpecialistRegistration(
        name="Western Disturbance Specialist",
        module_path="backend/app/builder2/western_disturbance_specialist.py",
        status=SpecialistStatus.FORMULA_BASELINE,
        feature_flag="ENABLE_WESTERN_DISTURBANCE_SPECIALIST",
        hazard_type="western_disturbance",
        is_formula=True,
        has_trained_artifact=False,
        evidence_package_path=None,
        promotion_gate_status="UNPROMOTED_FORMULA",
        reviewer_signoff=None,
        target_definition="WD orographic precipitation and trough timing error",
        data_split_info="NOT_TRAINED (deterministic heuristic rules)",
        model_sha256=None,
        target_manifest_path="data/western_disturbance_target_manifest.json",
        bust_formula="Precip error > 20mm OR Snow equiv error > 15cm OR Timing error > 6h",
        evidence_tier="FORMULA_BASELINE",
    ),
    "heatwave": SpecialistRegistration(
        name="Heatwave Reliability Specialist",
        module_path="backend/app/builder2/heatwave_specialist.py",
        status=SpecialistStatus.FORMULA_BASELINE,
        feature_flag="ENABLE_HEATWAVE_SPECIALIST",
        hazard_type="heatwave",
        is_formula=True,
        has_trained_artifact=False,
        evidence_package_path=None,
        promotion_gate_status="UNPROMOTED_FORMULA",
        reviewer_signoff=None,
        target_definition="Maximum temperature forecast error >= 3.0C during heatwave conditions",
        data_split_info="NOT_TRAINED (deterministic heuristic rules)",
        model_sha256=None,
        target_manifest_path="data/heatwave_target_manifest.json",
        bust_formula="|Tmax_forecast - Tmax_observed| >= 3.0C OR threshold breach > 45C",
        evidence_tier="FORMULA_BASELINE",
    ),
    "spatial_reliability": SpecialistRegistration(
        name="Spatial Reliability Engine",
        module_path="backend/app/builder2/spatial_reliability_engine.py",
        status=SpecialistStatus.EXPERIMENTAL,
        feature_flag="ENABLE_SPATIAL_ENGINE",
        hazard_type="spatial_error_field",
        is_formula=True,
        has_trained_artifact=False,
        evidence_package_path=None,
        promotion_gate_status="EXPERIMENTAL_RESEARCH",
        reviewer_signoff=None,
        target_definition="Spatial displacement error vectors",
        data_split_info="EXPERIMENTAL_SYNTHETIC",
        model_sha256=None,
        target_manifest_path="data/spatial_target_manifest.json",
        bust_formula="Centroid displacement > 75km OR Swath overlap IoU < 0.30",
        evidence_tier="EXPERIMENTAL_HEURISTIC",
    ),
    "compound_hazard": SpecialistRegistration(
        name="Compound Hazard Engine",
        module_path="backend/app/builder2/compound_hazard_engine.py",
        status=SpecialistStatus.EXPERIMENTAL,
        feature_flag="ENABLE_COMPOUND_HAZARD",
        hazard_type="compound_events",
        is_formula=True,
        has_trained_artifact=False,
        evidence_package_path=None,
        promotion_gate_status="EXPERIMENTAL_RESEARCH",
        reviewer_signoff=None,
        target_definition="Joint co-occurrence of multiple hazard thresholds",
        data_split_info="EXPERIMENTAL_HEURISTIC",
        model_sha256=None,
        target_manifest_path=None,
        bust_formula="Joint co-occurrence failure across 2+ simultaneous hazard thresholds",
        evidence_tier="EXPERIMENTAL_HEURISTIC",
    ),
    "common_mode": SpecialistRegistration(
        name="Common Mode Detector",
        module_path="backend/app/builder2/common_mode_detector.py",
        status=SpecialistStatus.EXPERIMENTAL,
        feature_flag="ENABLE_COMMON_MODE",
        hazard_type="common_mode_failure",
        is_formula=True,
        has_trained_artifact=False,
        evidence_package_path=None,
        promotion_gate_status="EXPERIMENTAL_RESEARCH",
        reviewer_signoff=None,
        target_definition="Multi-model simultaneous failure detection",
        data_split_info="EXPERIMENTAL_HEURISTIC",
        model_sha256=None,
        target_manifest_path=None,
        bust_formula="Multi-model simultaneous failure across 2+ NWP ensemble members",
        evidence_tier="EXPERIMENTAL_HEURISTIC",
    ),
    "cross_system": SpecialistRegistration(
        name="Cross-System Transfer Engine",
        module_path="backend/app/builder2/cross_system_transfer_engine.py",
        status=SpecialistStatus.EXPERIMENTAL,
        feature_flag="ENABLE_CROSS_SYSTEM",
        hazard_type="cross_system_transfer",
        is_formula=True,
        has_trained_artifact=False,
        evidence_package_path=None,
        promotion_gate_status="EXPERIMENTAL_RESEARCH",
        reviewer_signoff=None,
        target_definition="Transferability of failure motifs between NWP systems",
        data_split_info="EXPERIMENTAL_HEURISTIC",
        model_sha256=None,
        target_manifest_path=None,
        bust_formula="Delta Brier > 0.035 under zero-shot transfer across aligned NWP systems",
        evidence_tier="EXPERIMENTAL_HEURISTIC",
    ),
    "severe_wind": SpecialistRegistration(
        name="Severe Wind Specialist",
        module_path="backend/app/builder2/severe_wind_specialist.py",
        status=SpecialistStatus.QUARANTINED,
        feature_flag="ENABLE_SEVERE_WIND_SPECIALIST",
        hazard_type="severe_wind",
        is_formula=False,
        has_trained_artifact=False,
        evidence_package_path=None,
        promotion_gate_status="QUARANTINED_MISSING_PACKAGE",
        reviewer_signoff=None,
        target_definition="Surface wind gust bust >= 15 m/s",
        data_split_info="MISSING_FUTURE_BY_DESIGN",
        model_sha256=None,
        target_manifest_path=None,
        bust_formula="Surface wind gust bust >= 15 m/s",
        evidence_tier="QUARANTINED",
    ),
}


def export_specialist_evidence_ledger() -> List[Dict[str, Any]]:
    """Export machine-readable specialist evidence ledger matching docs/science-evidence/specialist_evidence_ledger.csv."""
    rows = []
    for key, spec in SPECIALIST_REGISTRY.items():
        rows.append({
            "specialist_id": key,
            "name": spec.name,
            "hazard_family": spec.hazard_type,
            "status": spec.status.value,
            "evidence_tier": spec.evidence_tier,
            "is_formula": spec.is_formula,
            "has_trained_artifact": spec.has_trained_artifact,
            "target_definition": spec.target_definition or "N/A",
            "bust_formula": spec.bust_formula or "N/A",
            "target_manifest": spec.target_manifest_path or "N/A",
            "evidence_package": spec.evidence_package_path or "N/A",
            "promotion_gate_status": spec.promotion_gate_status or "N/A",
            "active_in_production": is_specialist_active_in_production(key),
        })
    return rows


def get_specialist(name: str) -> Optional[SpecialistRegistration]:
    """Retrieve specialist registration by key."""
    return SPECIALIST_REGISTRY.get(name.lower())


def is_specialist_active_in_production(name: str) -> bool:
    """A specialist can ONLY be active in production if:
    1. It is registered.
    2. Its feature flag is explicitly enabled.
    3. Its status is PROMOTED.
    
    Formula baselines and experimental engines are NEVER active in the production path.
    """
    spec = get_specialist(name)
    if spec is None:
        return False
    if not is_feature_enabled(spec.feature_flag):
        return False
    if spec.status != SpecialistStatus.PROMOTED:
        return False
    return True


def evaluate_promotion_eligibility(reg: SpecialistRegistration) -> Tuple[bool, List[str]]:
    """Strictly evaluate Gate G8 promotion criteria.
    
    No specialist enters production without:
    - Trained artifact or documented formula
    - Verified evidence package path
    - Independent reviewer signoff
    - Verified model sha256
    - Passed promotion gate status
    """
    blockers: List[str] = []

    if reg.status == SpecialistStatus.QUARANTINED:
        blockers.append(f"{reg.name} is QUARANTINED and ineligible for promotion.")
        return False, blockers

    if not reg.has_trained_artifact and reg.is_formula:
        blockers.append(
            f"{reg.name} is a deterministic formula baseline. "
            "Formulas must remain labeled FORMULA_BASELINE and cannot be promoted as trained ML models."
        )

    if not reg.evidence_package_path:
        blockers.append(f"{reg.name} lacks an independent evidence package path.")

    if not reg.reviewer_signoff:
        blockers.append(f"{reg.name} lacks independent reviewer signoff.")

    if reg.promotion_gate_status != "PASSED":
        blockers.append(
            f"{reg.name} promotion gate status is '{reg.promotion_gate_status}', required: 'PASSED'."
        )

    if reg.has_trained_artifact and not reg.model_sha256:
        blockers.append(f"{reg.name} has trained artifact but missing model_sha256 checksum.")

    is_eligible = len(blockers) == 0
    return is_eligible, blockers
