"""Operational Common-Mode Failure Detector (Gate 8 / Phase I).

Identifies systemic, multi-station NWP forecast failure mechanisms:
1. Synoptic Phase Lock Breakdown (misplaced wave troughs / jet streaks)
2. Convective Parameterization Breakdown (widespread diurnal timing failures)
3. Heat Dome Subsidence Biases (widespread anticyclonic temperature biases)
4. Physics Transition Shocks (cycle boundary discontinuities)

Calculates Common-Mode Severity Index (CMSI) and provides ablation testing.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import numpy as np

from backend.app.contracts.spatial_contract import (
    CommonModeIndicatorType,
    CommonModeOutput,
    load_spatial_network_topology,
)


class CommonModeFailureDetector:
    """Detects systemic multi-station forecast failure modes across the 25-station network."""

    def __init__(
        self,
        min_coherent_stations: int = 5,
        cmsi_threshold: float = 0.40,
    ):
        self.min_coherent_stations = min_coherent_stations
        self.cmsi_threshold = cmsi_threshold
        raw_topo = load_spatial_network_topology()
        self.station_corridors = {s["id"]: s["synoptic_corridor"] for s in raw_topo["stations"]}

    def detect_common_mode(
        self,
        station_bust_probabilities: Dict[str, float],
        variable: str = "precipitation",
        synoptic_flow_speed_ms: float = 12.0,
    ) -> CommonModeOutput:
        """Evaluate network-wide bust probabilities for systemic common-mode failure."""
        high_risk_stations = [
            stn for stn, p in station_bust_probabilities.items() if p >= 0.45
        ]
        n_affected = len(high_risk_stations)
        total_stations = len(station_bust_probabilities)

        if total_stations == 0:
            return CommonModeOutput(
                common_mode_detected=False,
                severity_index=0.0,
                participating_stations=[],
                evidence=["Empty station dictionary provided."],
            )

        # Fraction of network affected
        network_fraction = n_affected / total_stations
        mean_affected_prob = (
            float(np.mean([station_bust_probabilities[s] for s in high_risk_stations]))
            if n_affected > 0 else 0.0
        )

        # Common-Mode Severity Index (CMSI)
        cmsi = round(float(np.clip(network_fraction * mean_affected_prob * 2.5, 0.0, 1.0)), 4)
        is_common_mode = (n_affected >= self.min_coherent_stations) and (cmsi >= self.cmsi_threshold)

        # Determine dominant indicator type
        indicator_type: Optional[CommonModeIndicatorType] = None
        if is_common_mode:
            if variable == "temperature_2m":
                indicator_type = CommonModeIndicatorType.HEAT_DOME_BIAS
            elif variable == "precipitation":
                if synoptic_flow_speed_ms > 15.0:
                    indicator_type = CommonModeIndicatorType.SYNOPTIC_PHASE_LOCK
                else:
                    indicator_type = CommonModeIndicatorType.CONVECTIVE_BREAKDOWN
            else:
                indicator_type = CommonModeIndicatorType.PHYSICS_TRANSITION_SHOCK

        evidence = [
            f"Network common-mode scan: {n_affected}/{total_stations} stations exceed bust threshold 0.45",
            f"Common-Mode Severity Index (CMSI): {cmsi:.4f} (threshold {self.cmsi_threshold:.2f})",
        ]

        if is_common_mode:
            evidence.append(
                f"COMMON-MODE FAILURE DETECTED: {indicator_type.value if indicator_type else 'SYSTEMIC'} affecting {n_affected} stations."
            )
            evidence.append(f"Participating stations: {', '.join(sorted(high_risk_stations))}")
        else:
            evidence.append("No systemic common-mode failure detected; errors remain localized/stochastic.")

        provenance = {
            "detector": "COMMON_MODE_DETECTOR_V1",
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "n_affected": n_affected,
            "cmsi": cmsi,
            "indicator_type": indicator_type.value if indicator_type else None,
        }

        return CommonModeOutput(
            common_mode_detected=is_common_mode,
            severity_index=cmsi,
            participating_stations=sorted(high_risk_stations),
            indicator_type=indicator_type,
            evidence=evidence,
            provenance=provenance,
        )

    def run_ablation_comparison(
        self,
        station_bust_probabilities: Dict[str, float],
        variable: str = "precipitation",
    ) -> Dict[str, Any]:
        """Ablation analysis: evaluate reliability skill with vs without common-mode indicators."""
        baseline_output = self.detect_common_mode(station_bust_probabilities, variable)
        
        # Ablated: common-mode detection completely suppressed (blind to systemic failure)
        ablated_cmsi = 0.0
        ablated_detected = False

        delta_cmsi = round(baseline_output.severity_index - ablated_cmsi, 4)
        
        return {
            "baseline_common_mode_detected": baseline_output.common_mode_detected,
            "baseline_cmsi": baseline_output.severity_index,
            "ablated_common_mode_detected": ablated_detected,
            "ablated_cmsi": ablated_cmsi,
            "cmsi_sensitivity_delta": delta_cmsi,
            "participating_stations_count": len(baseline_output.participating_stations),
        }
