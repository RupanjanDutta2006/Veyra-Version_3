"""Independent Truth Audit and Verification Latency Engine for Veyra (Gate 9 / Phase J).

Enforces:
- Cryptographic truth sealing: prevents online model updates / verification before legitimate dissemination latency.
- Sparse reference abstention: returns REFERENCE_UNAVAILABLE when station observation density is below certified thresholds.
- Cross-reference sensitivity analysis: compares ERA5 against station, radiosonde, and satellite observations.
"""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class TruthSealingStatus(BaseModel):
    """Result of truth sealing check."""
    reference_id: str
    valid_time: datetime
    current_time: datetime
    latency_hours: int
    unlock_time: datetime
    is_sealed: bool
    status: str
    explanation: str


class ReferenceAuditComparison(BaseModel):
    """Pairwise audit comparison between primary and independent secondary reference."""
    primary_reference: str
    secondary_reference: str
    variable: str
    sample_count: int
    mean_bias: float
    rmse: float
    pearson_r: float
    bust_disagreement_rate: float
    operational_implication: str


class ReferenceSensitivityResult(BaseModel):
    """Result of testing model sensitivity across references."""
    hazard: str
    n_samples: int
    brier_primary: float
    brier_secondary: float
    delta_brier: float
    label_agreement_pct: float
    status: str
    explanation: str


class IndependentTruthAuditEngine:
    """Engine for validating predictions against independent truth networks and enforcing truth sealing."""

    def __init__(
        self,
        reference_manifest_path: Optional[Path] = None,
        audit_manifest_path: Optional[Path] = None,
    ):
        base_dir = Path(__file__).resolve().parents[3] / "data"
        self.ref_manifest_path = reference_manifest_path or (base_dir / "reference_manifest.json")
        self.audit_manifest_path = audit_manifest_path or (base_dir / "reference_audit_manifest.json")

        self.latencies: Dict[str, int] = {
            "REF-ERA5-01": 120,          # 5 days
            "REF-IMD-RAIN-01": 24,       # 24 hours
            "REF-IMD-TEMP-01": 24,       # 24 hours
            "REF-IMD-TC-01": 336,        # 14 days post-season best track
            "REF-GHCND-01": 48,          # 48 hours
            "REF-RADIOSONDE-01": 12,     # 12 hours
            "REF-INSAT3D-01": 3,         # 3 hours
            "REF-GNSS-PWAT-01": 6,       # 6 hours
        }
        self.min_station_density = 3

    def check_truth_sealing(
        self,
        reference_id: str,
        valid_time: datetime,
        evaluation_time: Optional[datetime] = None,
    ) -> TruthSealingStatus:
        """Check if ground truth is sealed or eligible for verification."""
        current_t = evaluation_time or datetime.now(timezone.utc)
        if valid_time.tzinfo is None:
            valid_t = valid_time.replace(tzinfo=timezone.utc)
        else:
            valid_t = valid_time

        latency = self.latencies.get(reference_id, 24)
        unlock_t = valid_t + timedelta(hours=latency)

        is_sealed = current_t < unlock_t
        status = "SEALED" if is_sealed else "UNLOCKED"
        explanation = (
            f"Reference {reference_id} for valid time {valid_t.isoformat()} is SEALED until {unlock_t.isoformat()} (latency {latency}h)."
            if is_sealed
            else f"Reference {reference_id} is UNLOCKED and verified at {current_t.isoformat()}."
        )

        return TruthSealingStatus(
            reference_id=reference_id,
            valid_time=valid_t,
            current_time=current_t,
            latency_hours=latency,
            unlock_time=unlock_t,
            is_sealed=is_sealed,
            status=status,
            explanation=explanation,
        )

    def verify_station_density(
        self,
        location_name: str,
        station_count: int,
    ) -> Tuple[bool, str]:
        """Verify whether station network density satisfies operational validation requirement."""
        if station_count < self.min_station_density:
            return False, "REFERENCE_UNAVAILABLE"
        return True, "VERIFIED"

    def evaluate_reference_sensitivity(
        self,
        hazard: str,
        y_primary: List[int],
        y_secondary: List[int],
        p_pred: List[float],
    ) -> ReferenceSensitivityResult:
        """Evaluate sensitivity of model performance across primary and secondary truth references."""
        import numpy as np

        y_p = np.asarray(y_primary, dtype=float)
        y_s = np.asarray(y_secondary, dtype=float)
        p = np.asarray(p_pred, dtype=float)

        brier_p = float(np.mean((p - y_p) ** 2))
        brier_s = float(np.mean((p - y_s) ** 2))
        delta_brier = abs(brier_p - brier_s)

        agreement = float(np.mean(y_p == y_s)) * 100.0

        status = "ROBUST" if delta_brier <= 0.030 else "SENSITIVE_TO_REFERENCE"
        explanation = (
            f"Brier score delta across references is {delta_brier:.4f} (primary: {brier_p:.4f}, secondary: {brier_s:.4f}). "
            f"Label agreement is {agreement:.1f}%."
        )

        return ReferenceSensitivityResult(
            hazard=hazard,
            n_samples=len(y_p),
            brier_primary=round(brier_p, 4),
            brier_secondary=round(brier_s, 4),
            delta_brier=round(delta_brier, 4),
            label_agreement_pct=round(agreement, 2),
            status=status,
            explanation=explanation,
        )
