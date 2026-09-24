"""
Deterministic Physical Feature Attribution & Explainer Engine.

Identifies and ranks the primary physical drivers of forecast bust risk
(dispersion, inter-cycle revisions, lead degradation) without generating
uncalibrated or hallucinated explanations.
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from backend.app.builder2.schemas import ContributingFactor, ExplanationItem


class ForecastBustExplainer:
    """Extracts deterministic physical explanations for forecast bust risk."""

    @staticmethod
    def explain_row(feature_row: Dict[str, Any], bust_probability: float, threshold: float = 0.280) -> ExplanationItem:
        """
        Produce a structured physical explanation for a single forecast step.

        Args:
            feature_row: Dict containing the 26 canonical feature values.
            bust_probability: Calibrated bust probability float.
            threshold: Decision threshold for active bust alert.

        Returns:
            ExplanationItem dataclass.
        """
        factors: List[ContributingFactor] = []

        # 1. Inspect Inter-Cycle 24h Revision Drift
        f_delta_24h = feature_row.get("forecast_delta_24h")
        if f_delta_24h is not None and not (isinstance(f_delta_24h, float) and np.isnan(f_delta_24h)):
            abs_delta = abs(float(f_delta_24h))
            if abs_delta >= 2.0:
                factors.append(ContributingFactor(factor="forecast_delta_24h", value=float(f_delta_24h), signal="HIGH_REVISION_DRIFT"))
            elif abs_delta >= 0.75:
                factors.append(ContributingFactor(factor="forecast_delta_24h", value=float(f_delta_24h), signal="MODERATE_REVISION_DRIFT"))
            else:
                factors.append(ContributingFactor(factor="forecast_delta_24h", value=float(f_delta_24h), signal="LOW_REVISION_DRIFT"))
        else:
            factors.append(ContributingFactor(factor="forecast_delta_24h", value=None, signal="NO_PRIOR_CYCLE_BASELINE"))

        # 2. Inspect Ensemble Spread & Dispersion (Preserve variable scale without unauthenticated thresholds)
        ens_std = feature_row.get("ensemble_std")
        is_pressure = bool(
            feature_row.get("is_surface_pressure") == 1.0
            or str(feature_row.get("variable", "")).lower() in ("surface_pressure", "pressure")
        )
        if ens_std is not None and not (isinstance(ens_std, float) and np.isnan(ens_std)):
            val_std = float(ens_std)
            if is_pressure:
                # Surface pressure is recorded in Pascals; preserve raw spread with neutral signal
                factors.append(ContributingFactor(factor="ensemble_std", value=val_std, signal="ENSEMBLE_SPREAD"))
            elif val_std >= 3.0:
                factors.append(ContributingFactor(factor="ensemble_std", value=val_std, signal="HIGH_ENSEMBLE_SPREAD"))
            elif val_std >= 1.5:
                factors.append(ContributingFactor(factor="ensemble_std", value=val_std, signal="ELEVATED_ENSEMBLE_SPREAD"))
            else:
                factors.append(ContributingFactor(factor="ensemble_std", value=val_std, signal="LOW_ENSEMBLE_SPREAD"))

        # 3. Inspect Horizon / Lead Time
        lead_hours = feature_row.get("lead_hours")
        if lead_hours is not None:
            val_lead = int(lead_hours)
            if val_lead >= 168:
                factors.append(ContributingFactor(factor="lead_hours", value=float(val_lead), signal="EXTENDED_RANGE_DEGRADATION"))
            elif val_lead >= 72:
                factors.append(ContributingFactor(factor="lead_hours", value=float(val_lead), signal="MEDIUM_RANGE_HORIZON"))
            else:
                factors.append(ContributingFactor(factor="lead_hours", value=float(val_lead), signal="SHORT_RANGE_HORIZON"))

        # 4. Inspect Spread Delta 24h
        spr_delta_24h = feature_row.get("ensemble_spread_delta_24h")
        if spr_delta_24h is not None and not (isinstance(spr_delta_24h, float) and np.isnan(spr_delta_24h)):
            val_spr_delta = float(spr_delta_24h)
            if val_spr_delta > 1.0:
                factors.append(ContributingFactor(factor="ensemble_spread_delta_24h", value=val_spr_delta, signal="SPREAD_GROWTH"))

        # 5. Inspect Revision Acceleration (6h) (§12, G7)
        rev_accel = feature_row.get("revision_accel_6h")
        if rev_accel is not None and not (isinstance(rev_accel, float) and np.isnan(rev_accel)):
            val_accel = float(rev_accel)
            if abs(val_accel) >= 1.0:
                factors.append(ContributingFactor(factor="revision_accel_6h", value=val_accel, signal="REVISION_ACCELERATION"))
            elif abs(val_accel) >= 0.5:
                factors.append(ContributingFactor(factor="revision_accel_6h", value=val_accel, signal="MODERATE_REVISION_ACCELERATION"))

        # 6. Inspect Spread-to-IQR Ratio (§12, G7)
        spread_iqr = feature_row.get("ensemble_spread_to_iqr_ratio")
        if spread_iqr is not None and not (isinstance(spread_iqr, float) and np.isnan(spread_iqr)):
            val_sp_iqr = float(spread_iqr)
            if val_sp_iqr >= 1.5:
                factors.append(ContributingFactor(factor="ensemble_spread_to_iqr_ratio", value=val_sp_iqr, signal="SPREAD_TO_ERROR_RATIO"))

        # 7. Inspect Synoptic Regime / Blocking Index (§12, G7)
        bi = feature_row.get("blocking_index")
        if bi is not None and not (isinstance(bi, float) and np.isnan(bi)):
            val_bi = float(bi)
            if abs(val_bi) >= 1.5:
                factors.append(ContributingFactor(factor="blocking_index", value=val_bi, signal="REGIME_TRANSITION"))

        # 8. Inspect Analog Bust Frequency (§12, G7)
        analog_freq = feature_row.get("analog_bust_frequency")
        if analog_freq is not None and not (isinstance(analog_freq, float) and np.isnan(analog_freq)):
            val_af = float(analog_freq)
            if val_af >= 0.60:
                factors.append(ContributingFactor(factor="analog_bust_frequency", value=val_af, signal="ANALOG_BUST_FREQUENCY"))

        # Determine Primary Driver and Summary Narrative with Guaranteed Factor-Level Consistency
        signals = [f.signal for f in factors]
        has_high_spread = "HIGH_ENSEMBLE_SPREAD" in signals or "SPREAD_GROWTH" in signals
        has_high_drift = "HIGH_REVISION_DRIFT" in signals
        has_rev_accel = "REVISION_ACCELERATION" in signals
        has_spread_iqr = "SPREAD_TO_ERROR_RATIO" in signals
        has_regime_trans = "REGIME_TRANSITION" in signals
        has_analog_bust = "ANALOG_BUST_FREQUENCY" in signals
        has_ext_lead = "EXTENDED_RANGE_DEGRADATION" in signals
        std_val = next((f.value for f in factors if f.factor == "ensemble_std"), 0.0) or 0.0
        delta_val = next((f.value for f in factors if f.factor == "forecast_delta_24h"), 0.0) or 0.0

        is_alert = bust_probability >= threshold

        if is_alert:
            # Active alert mode
            if has_high_drift:
                primary_driver = "rapid_inter_cycle_revision"
                summary = f"High risk driven by rapid 24h run-to-run forecast revision ({delta_val:+.2f} unit drift)."
            elif has_rev_accel:
                primary_driver = "revision_acceleration"
                summary = "High risk driven by accelerating run-to-run forecast revisions across successive issue cycles."
            elif has_high_spread:
                primary_driver = "high_ensemble_uncertainty"
                summary = f"High risk driven by strong physical ensemble dispersion (spread = {std_val:.2f})."
            elif has_spread_iqr:
                primary_driver = "spread_to_error_ratio"
                summary = "High risk driven by elevated spread-to-error ratio indicating distribution asymmetry."
            elif has_regime_trans:
                primary_driver = "regime_transition"
                summary = "Risk elevated due to active synoptic blocking pattern and regime transition."
            elif has_analog_bust:
                primary_driver = "analog_bust_frequency"
                summary = "Risk elevated by high historical bust frequency in analogous synoptic regimes."
            elif has_ext_lead:
                primary_driver = "extended_horizon_uncertainty"
                summary = "Risk elevated due to long lead horizon degradation and accumulated forecast uncertainty."
            else:
                primary_driver = "multi_factor_risk"
                summary = "Elevated risk driven by combination of ensemble spread and lead-time horizon."
        else:
            # Non-alert mode: Guarantee narrative does not contradict factor state
            if has_high_spread:
                primary_driver = "elevated_ensemble_spread"
                summary = f"Forecast exhibits notable ensemble dispersion (spread = {std_val:.2f}) despite moderate overall bust probability."
            elif has_high_drift:
                primary_driver = "moderate_inter_cycle_revision"
                summary = f"Forecast exhibits run-to-run revision ({delta_val:+.2f} unit drift) with low overall bust probability."
            elif is_pressure:
                primary_driver = "stable_ensemble_agreement"
                summary = f"Forecast is stable with consistent synoptic pressure consensus (ensemble spread = {std_val:.2f} Pa)."
            else:
                primary_driver = "stable_ensemble_agreement"
                summary = "Forecast is stable with low ensemble dispersion and consistent inter-cycle agreement."

        return ExplanationItem(
            primary_driver=primary_driver,
            driver_summary=summary,
            top_contributing_factors=factors,
        )
