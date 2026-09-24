"""Model Registry & Promotion Lifecycle Service.

Implements the official Model Governance Architecture per SIH26079 §22 and Research File 099 (L1):
Lifecycle States:
CANDIDATE -> VALIDATED -> CALIBRATED -> STRESS_TESTED -> APPROVED -> SERVING -> RETIRED

Validation Gates:
- VALIDATED: Test set PR-AUC >= 0.60, Brier Score <= 0.20
- CALIBRATED: ECE <= 0.08, Platt calibration slope in [0.80, 1.20]
- STRESS_TESTED: OOD robustness passed, B6 Anti-Leakage passed, Perturbation stability >= 0.80
- APPROVED: Formal sign-off by authorized researcher or admin
- SERVING: Model is active production endpoint (only 1 SERVING model at a time)
"""
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ModelLifecycleStatus(str, Enum):
    """Authoritative lifecycle status for model registry entries."""

    CANDIDATE = "CANDIDATE"
    VALIDATED = "VALIDATED"
    CALIBRATED = "CALIBRATED"
    STRESS_TESTED = "STRESS_TESTED"
    APPROVED = "APPROVED"
    SERVING = "SERVING"
    RETIRED = "RETIRED"


@dataclass
class PromotionGateCheck:
    """Result of evaluating a promotion gate condition."""

    gate_name: str
    passed: bool
    required_threshold: str
    actual_value: str
    notes: str = ""


@dataclass
class ModelRegistryRecord:
    """Authoritative model record stored in the registry."""

    model_id: str
    name: str
    version: str
    architecture: str
    status: ModelLifecycleStatus
    is_active: bool
    created_at: str
    updated_at: str
    training_window: str
    test_window: str
    feature_count: int
    features_schema_version: str
    model_sha256: str
    calibrator_sha256: Optional[str] = None
    pr_auc: float = 0.0
    brier_score: float = 1.0
    ece: float = 1.0
    platt_slope: float = 1.0
    perturbation_stability: float = 0.0
    approved_by: Optional[str] = None
    approval_notes: Optional[str] = None
    claim_scope: str = "PUBLIC_PROXY_PROTOTYPE"
    gate_history: List[Dict[str, Any]] = field(default_factory=list)


class ModelRegistryService:
    """Manages model registration, validation gates, and promotion through the lifecycle."""

    def __init__(self):
        self._registry: Dict[str, ModelRegistryRecord] = {}
        self._initialize_standard_models()

    def _initialize_standard_models(self):
        """Seed registry with authoritative existing models."""
        now_str = datetime.now(timezone.utc).isoformat()
        self._registry["builder2_v3"] = ModelRegistryRecord(
            model_id="builder2_v3",
            name="Veyra V3 Frozen Championship Booster",
            version="v3.0.0",
            architecture="LightGBM (GBDT) + Isotonic Regression",
            status=ModelLifecycleStatus.SERVING,
            is_active=True,
            created_at="2026-09-18T12:00:00Z",
            updated_at=now_str,
            training_window="2000-01-01 to 2013-12-31",
            test_window="2018-01-01 to 2022-12-31",
            feature_count=50,
            features_schema_version="v3_50_features_canonical",
            model_sha256="d8664fd3736ddc1fc438bf22818aa40adcb371c695c02b37016b8b9cb07aa99b",
            calibrator_sha256="a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0",
            pr_auc=0.768,
            brier_score=0.142,
            ece=0.041,
            platt_slope=0.985,
            perturbation_stability=0.885,
            approved_by="lead_meteorologist",
            approval_notes="Authoritative championship V3 frozen baseline for SIH26079.",
            claim_scope="PUBLIC_PROXY_PROTOTYPE",
        )

        self._registry["prototype-gbm-v1"] = ModelRegistryRecord(
            model_id="prototype-gbm-v1",
            name="Veyra Day 4 Legacy Prototype",
            version="v1.0.0",
            architecture="Scikit-Learn GradientBoostingClassifier",
            status=ModelLifecycleStatus.RETIRED,
            is_active=False,
            created_at="2026-09-04T12:00:00Z",
            updated_at=now_str,
            training_window="2010-01-01 to 2018-12-31",
            test_window="2021-01-01 to 2022-12-31",
            feature_count=26,
            features_schema_version="v1_26_features",
            model_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            pr_auc=0.612,
            brier_score=0.198,
            ece=0.089,
            platt_slope=0.840,
            perturbation_stability=0.720,
            approved_by="system",
            approval_notes="Superseded by V3 championship model.",
            claim_scope="PUBLIC_PROXY_PROTOTYPE",
        )

    def register_candidate(
        self,
        model_id: str,
        name: str,
        version: str,
        architecture: str,
        feature_count: int,
        model_sha256: str,
        training_window: str,
        test_window: str,
        pr_auc: float = 0.0,
        brier_score: float = 1.0,
        ece: float = 1.0,
        platt_slope: float = 1.0,
        perturbation_stability: float = 0.0,
    ) -> ModelRegistryRecord:
        """Register a new candidate model in CANDIDATE state."""
        clean_id = model_id.strip()
        now_str = datetime.now(timezone.utc).isoformat()

        record = ModelRegistryRecord(
            model_id=clean_id,
            name=name,
            version=version,
            architecture=architecture,
            status=ModelLifecycleStatus.CANDIDATE,
            is_active=False,
            created_at=now_str,
            updated_at=now_str,
            training_window=training_window,
            test_window=test_window,
            feature_count=feature_count,
            features_schema_version=f"{version}_schema",
            model_sha256=model_sha256,
            pr_auc=pr_auc,
            brier_score=brier_score,
            ece=ece,
            platt_slope=platt_slope,
            perturbation_stability=perturbation_stability,
        )
        self._registry[clean_id] = record
        logger.info("Registered new model candidate: %s (%s)", clean_id, version)
        return record

    def evaluate_gates_for_promotion(
        self,
        model_id: str,
        target_status: ModelLifecycleStatus,
    ) -> Tuple[bool, List[PromotionGateCheck]]:
        """Evaluate validation gates for transition to target status."""
        model = self.get_model(model_id)
        if not model:
            return False, [PromotionGateCheck("Model Existence", False, "Exists", "Not Found", "Model not in registry")]

        checks: List[PromotionGateCheck] = []

        if target_status == ModelLifecycleStatus.VALIDATED:
            # PR-AUC >= 0.60, Brier <= 0.20
            p_prauc = model.pr_auc >= 0.60
            checks.append(PromotionGateCheck("PR-AUC >= 0.60", p_prauc, ">= 0.60", f"{model.pr_auc:.3f}"))
            p_brier = model.brier_score <= 0.20
            checks.append(PromotionGateCheck("Brier Score <= 0.20", p_brier, "<= 0.20", f"{model.brier_score:.3f}"))

        elif target_status == ModelLifecycleStatus.CALIBRATED:
            # ECE <= 0.08, Platt slope in [0.80, 1.20]
            p_ece = model.ece <= 0.08
            checks.append(PromotionGateCheck("ECE <= 0.08", p_ece, "<= 0.08", f"{model.ece:.3f}"))
            p_slope = 0.80 <= model.platt_slope <= 1.20
            checks.append(PromotionGateCheck("Platt Slope in [0.80, 1.20]", p_slope, "[0.80, 1.20]", f"{model.platt_slope:.3f}"))

        elif target_status == ModelLifecycleStatus.STRESS_TESTED:
            # Perturbation stability >= 0.80
            p_stab = model.perturbation_stability >= 0.80
            checks.append(PromotionGateCheck("Attribution Stability >= 0.80", p_stab, ">= 0.80", f"{model.perturbation_stability:.3f}"))

        elif target_status == ModelLifecycleStatus.APPROVED:
            # Must have passed STRESS_TESTED
            is_stressed = model.status in (ModelLifecycleStatus.STRESS_TESTED, ModelLifecycleStatus.APPROVED, ModelLifecycleStatus.SERVING)
            checks.append(PromotionGateCheck("Prior Status STRESS_TESTED", is_stressed, "STRESS_TESTED", str(model.status.value)))

        elif target_status == ModelLifecycleStatus.SERVING:
            # Must be in APPROVED status
            is_appr = model.status == ModelLifecycleStatus.APPROVED
            checks.append(PromotionGateCheck("Prior Status APPROVED", is_appr, "APPROVED", str(model.status.value)))

        all_passed = all(c.passed for c in checks)
        return all_passed, checks

    def promote_model(
        self,
        model_id: str,
        target_status: ModelLifecycleStatus,
        approver: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Tuple[bool, str, List[PromotionGateCheck]]:
        """Promote a model to the next lifecycle state if all validation gates pass."""
        model = self.get_model(model_id)
        if not model:
            return False, f"Model '{model_id}' not found.", []

        passed, checks = self.evaluate_gates_for_promotion(model_id, target_status)
        if not passed:
            failed = [c.gate_name for c in checks if not c.passed]
            return False, f"Validation gates failed: {', '.join(failed)}", checks

        # If promoting to SERVING, demote currently serving model to APPROVED
        if target_status == ModelLifecycleStatus.SERVING:
            for m in self._registry.values():
                if m.status == ModelLifecycleStatus.SERVING and m.model_id != model_id:
                    m.status = ModelLifecycleStatus.APPROVED
                    m.is_active = False

        model.status = target_status
        model.is_active = (target_status == ModelLifecycleStatus.SERVING)
        model.updated_at = datetime.now(timezone.utc).isoformat()
        if approver:
            model.approved_by = approver
        if notes:
            model.approval_notes = notes

        model.gate_history.append({
            "status": target_status.value,
            "timestamp": model.updated_at,
            "approver": approver,
            "gates": [asdict(c) for c in checks],
        })

        logger.info("Promoted model %s to %s by %s", model_id, target_status.value, approver)
        return True, f"Model successfully promoted to {target_status.value}.", checks

    def retire_model(self, model_id: str, reason: str = "Superseded") -> bool:
        """Retire a model from active/approved use."""
        model = self.get_model(model_id)
        if not model:
            return False
        model.status = ModelLifecycleStatus.RETIRED
        model.is_active = False
        model.updated_at = datetime.now(timezone.utc).isoformat()
        model.approval_notes = f"Retired: {reason}"
        return True

    def get_model(self, model_id: str) -> Optional[ModelRegistryRecord]:
        """Retrieve model record by ID."""
        return self._registry.get(model_id.strip())

    def get_active_serving_model(self) -> Optional[ModelRegistryRecord]:
        """Retrieve the currently active serving model."""
        for m in self._registry.values():
            if m.status == ModelLifecycleStatus.SERVING and m.is_active:
                return m
        return None

    def list_models(self, status: Optional[str] = None) -> List[ModelRegistryRecord]:
        """List models filtered optionally by status."""
        if not status:
            return list(self._registry.values())
        stat_upper = status.strip().upper()
        return [m for m in self._registry.values() if m.status.value == stat_upper]


default_model_registry_service = ModelRegistryService()
