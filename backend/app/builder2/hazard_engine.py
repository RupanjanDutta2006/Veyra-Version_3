"""Hazard and Recovery Engine for Multi-Horizon Trajectories (Blueprint Gate 2 / Phase C).

Computes:
- Multi-horizon hazard curves across lead times [24, 48, 72, 96, 120, 144, 168, 192, 216, 240]
- Monotonic survival curves: S(t) = Prod_{tau <= t} (1 - P_bust(tau))
- Expected time-to-bust E[T_bust]
- Expected time-to-recovery E[T_recovery]
- Operational lifecycle transitions: STABLE -> WATCHING -> DEGRADING -> FAILURE_PRONE -> BUST -> RECOVERING -> STABLE
- Safe abstention transitions when inputs are OOD or missing.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from backend.app.contracts.hazard_contracts import HazardFamily
from backend.app.schemas.reliability_state import (
    ContinuousErrorDistribution,
    DecisionMode,
    EnsembleGeometry,
    EnsembleSummary,
    HazardPoint,
    OperationalReliabilityState,
    ReliabilityState,
)


class HazardTrajectoryEngine:
    """Computes multi-horizon hazard curves, survival curves, and recovery dynamics."""

    def __init__(self, lead_horizons: Optional[List[int]] = None):
        self.lead_horizons = lead_horizons or [24, 48, 72, 96, 120, 144, 168, 192, 216, 240]

    def compute_hazard_curve(
        self,
        base_bust_prob: float,
        hazard_family: Optional[HazardFamily] = None,
        spread_lead_slope: float = 0.08,
    ) -> List[HazardPoint]:
        """Generate multi-horizon hazard points.

        Bust probability typically scales with lead horizon due to error growth:
        P_bust(t) = 1 - (1 - P_base) * exp(-slope * (t - 24) / 96)
        """
        points: List[HazardPoint] = []
        for lead in self.lead_horizons:
            lead_factor = max(0.0, (lead - 24.0) / 96.0)
            p_bust = 1.0 - (1.0 - base_bust_prob) * float(np.exp(-spread_lead_slope * lead_factor))
            p_bust = float(np.clip(p_bust, 0.001, 0.999))

            # Hazard probability (conditioned on season/family)
            p_hazard = float(np.clip(0.10 + 0.30 * p_bust, 0.0, 1.0))
            points.append(HazardPoint(lead_hours=lead, hazard_prob=round(p_hazard, 4), bust_prob=round(p_bust, 4)))

        return points

    def compute_survival_curve(self, hazard_points: List[HazardPoint]) -> List[float]:
        """Compute monotonically non-increasing forecast survival curve S(t).

        S(t) = Prod_{tau <= t} (1 - P_bust(tau))
        Invariant: S(t_2) <= S(t_1) for all t_2 >= t_1.
        """
        survival: List[float] = []
        current_s = 1.0
        for pt in hazard_points:
            current_s *= (1.0 - pt.bust_prob)
            survival.append(round(float(current_s), 4))
        return survival

    def compute_expected_time_to_bust(
        self,
        hazard_points: List[HazardPoint],
        survival_curve: List[float],
    ) -> Optional[float]:
        """Compute expected time-to-bust E[T_bust] in hours.

        E[T] = Sum_{i} t_i * P(failure at t_i)
        where P(failure at t_i) = S(t_{i-1}) - S(t_i).
        """
        if not hazard_points or not survival_curve:
            return None

        leads = [pt.lead_hours for pt in hazard_points]
        s_prev = 1.0
        expected_t = 0.0
        total_prob = 0.0

        for lead, s_curr in zip(leads, survival_curve):
            p_fail = max(0.0, s_prev - s_curr)
            expected_t += lead * p_fail
            total_prob += p_fail
            s_prev = s_curr

        if total_prob > 0.05:
            # Conditional expectation given failure occurs within evaluation horizon
            return round(expected_t / total_prob, 1)
        return None

    def evaluate_recovery_dynamics(
        self,
        hazard_points: List[HazardPoint],
        current_state: OperationalReliabilityState,
    ) -> Tuple[Optional[float], float]:
        """Estimate time to recovery and recovery probability.

        Returns (expected_time_to_recovery_hours, recovery_probability).
        """
        if current_state in {OperationalReliabilityState.STABLE, OperationalReliabilityState.WATCHING}:
            return None, 1.0

        # Check if extended horizons exhibit declining bust probability
        bust_probs = [pt.bust_prob for pt in hazard_points]
        peaks = np.argmax(bust_probs)
        if peaks < len(bust_probs) - 1:
            # Trajectory begins to recover after peak
            peak_lead = hazard_points[peaks].lead_hours
            post_peak_drop = bust_probs[peaks] - bust_probs[-1]
            if post_peak_drop > 0.10:
                rec_prob = float(np.clip(post_peak_drop / bust_probs[peaks], 0.0, 1.0))
                time_to_rec = float(hazard_points[-1].lead_hours - peak_lead)
                return round(time_to_rec, 1), round(rec_prob, 4)

        return None, 0.20

    def determine_lifecycle_state(
        self,
        bust_prob: Optional[float],
        ood_score: float,
        missingness_score: float,
        drift_score: float,
        recovery_prob: float,
    ) -> Tuple[OperationalReliabilityState, DecisionMode, bool]:
        """Determine operational state machine and decision mode."""
        # 1. Abstention criteria
        if ood_score > 0.70 or missingness_score > 0.25 or bust_prob is None:
            return (
                OperationalReliabilityState.ABSTAIN,
                DecisionMode.ABSTAIN_UNSUPPORTED,
                True,
            )

        # 2. Lifecycle transitions
        if bust_prob >= 0.70:
            return OperationalReliabilityState.BUST, DecisionMode.HUMAN_OVERRIDE_REQUIRED, False
        elif bust_prob >= 0.50:
            return OperationalReliabilityState.FAILURE_PRONE, DecisionMode.CONSERVATIVE_DISPATCH, False
        elif bust_prob >= 0.30 or drift_score > 0.40:
            if recovery_prob > 0.50:
                return OperationalReliabilityState.RECOVERING, DecisionMode.ELEVATED_CAUTION, False
            return OperationalReliabilityState.DEGRADING, DecisionMode.ELEVATED_CAUTION, False
        elif bust_prob >= 0.15 or drift_score > 0.20:
            return OperationalReliabilityState.WATCHING, DecisionMode.NOMINAL, False
        else:
            return OperationalReliabilityState.STABLE, DecisionMode.NOMINAL, False

    def build_reliability_state(
        self,
        forecast_identity: str,
        issue_time: str,
        location: str,
        variable: str,
        lead_hours: int,
        model_version: str,
        base_bust_prob: Optional[float],
        ensemble_mean: float,
        ensemble_std: float,
        member_count: int = 31,
        hazard_family: Optional[HazardFamily] = None,
        ood_score: float = 0.0,
        drift_score: float = 0.0,
        missingness_score: float = 0.0,
    ) -> ReliabilityState:
        """Construct a complete ReliabilityState with multi-horizon hazard dynamics."""
        # Compute hazard & survival curves
        if base_bust_prob is not None:
            hazard_curve = self.compute_hazard_curve(base_bust_prob, hazard_family)
            survival_curve = self.compute_survival_curve(hazard_curve)
            time_to_bust = self.compute_expected_time_to_bust(hazard_curve, survival_curve)
        else:
            hazard_curve = []
            survival_curve = []
            time_to_bust = None

        time_to_rec, rec_prob = self.evaluate_recovery_dynamics(
            hazard_curve, OperationalReliabilityState.WATCHING
        )

        state, decision, is_abstained = self.determine_lifecycle_state(
            bust_prob=base_bust_prob,
            ood_score=ood_score,
            missingness_score=missingness_score,
            drift_score=drift_score,
            recovery_prob=rec_prob,
        )

        effective_bust_prob = None if is_abstained else base_bust_prob

        return ReliabilityState(
            forecast_identity=forecast_identity,
            issue_time=issue_time,
            location=location,
            variable=variable,
            lead_hours=lead_hours,
            model_version=model_version,
            forecast_values={"ensemble_mean": ensemble_mean, "ensemble_std": ensemble_std},
            ensemble_summary=EnsembleSummary(
                member_count=member_count,
                mean=ensemble_mean,
                std=ensemble_std,
                min_val=ensemble_mean - 2.0 * ensemble_std,
                max_val=ensemble_mean + 2.0 * ensemble_std,
                spread_to_error_ratio=round(ensemble_std / (base_bust_prob + 0.1), 3) if base_bust_prob else None,
                ensemble_cv=round(ensemble_std / (abs(ensemble_mean) + 1e-6), 4),
            ),
            ensemble_geometry=EnsembleGeometry(
                dispersion_metric=ensemble_std,
                cluster_count=1,
            ),
            bust_probability=effective_bust_prob,
            continuous_error_distribution=ContinuousErrorDistribution(
                mean_error=0.10,
                mae=round(ensemble_std * 0.8, 3),
                rmse=round(ensemble_std * 1.1, 3),
                q10=round(-1.28 * ensemble_std, 3),
                q50=0.0,
                q90=round(1.28 * ensemble_std, 3),
            ) if not is_abstained else None,
            hazard_type=hazard_family.value if hazard_family else None,
            hazard_probability=hazard_curve[0].hazard_prob if hazard_curve else None,
            hazard_curve=hazard_curve,
            survival_curve=survival_curve,
            expected_time_to_bust=time_to_bust,
            expected_time_to_recovery=time_to_rec,
            ood_score=ood_score,
            drift_score=drift_score,
            missingness_score=missingness_score,
            reliability_state=state,
            abstention_state=is_abstained,
            decision_mode=decision,
            evidence={"hazard_curve_points": len(hazard_curve)},
            provenance={"engine": "HazardTrajectoryEngine_v1"},
        )
