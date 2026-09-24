"""Failure Motifs and Archetypal Trajectory Classification (Blueprint Gate 2 / Phase C).

Defines canonical data-derived Failure Motifs across meteorological hazard families:
- MOTIF-HEAT-DOMING (Heatwave)
- MOTIF-CONVECTIVE-TRIGGER (Precipitation)
- MOTIF-TROUGH-PHASING (Western Disturbance)
- MOTIF-TC-RECURVATURE (Tropical Cyclone)
- MOTIF-DEPRESSION-SLOW (Monsoon & LPS)
- MOTIF-SQUALL-GUST (Severe Wind)

Provides MotifClassifier for matching forecast trajectories and precursor signals to archetypes.
"""

from enum import Enum
import json
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
from pydantic import BaseModel, Field

from backend.app.contracts.hazard_contracts import HazardFamily


class FailureMotif(BaseModel):
    """Canonical archetypal failure motif definition."""
    motif_id: str = Field(..., description="Unique motif identifier")
    motif_name: str = Field(..., description="Human-readable descriptive motif name")
    hazard_family: HazardFamily = Field(..., description="Associated hazard category")
    description: str = Field(..., description="Physical atmospheric mechanism")
    archetypal_trajectory: List[float] = Field(
        ..., description="Normalized error trajectory profile across lead hours [24, 48, 72, 96, 120]"
    )
    precursor_signals: List[str] = Field(..., description="Physical precursor indicators")
    mean_lead_to_bust_hours: float = Field(..., ge=0.0)
    recovery_probability_48h: float = Field(..., ge=0.0, le=1.0)


class MotifMatchResult(BaseModel):
    """Result of classifying a forecast trajectory against canonical failure motifs."""
    motif_id: str
    motif_name: str
    hazard_family: HazardFamily
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    precursors_matched: List[str]
    matched_precursor_ratio: float = Field(..., ge=0.0, le=1.0)
    narrative: str


# 6 Canonical Failure Motifs across core hazard families
CANONICAL_FAILURE_MOTIFS: List[FailureMotif] = [
    FailureMotif(
        motif_id="MOTIF-HEAT-DOMING",
        motif_name="Anticyclonic Heat Dome Subsidence",
        hazard_family=HazardFamily.HEATWAVE,
        description="Upper-tropospheric anticyclonic ridge stalls; persistent subsidence suppresses cloud cover and produces severe daytime sensible heating.",
        archetypal_trajectory=[0.10, 0.25, 0.55, 0.85, 0.95],
        precursor_signals=["HIGH_Z500_ANOMALY", "LOW_SOIL_MOISTURE", "CLEAR_SKY_SOLAR_EXCESS", "SUBSIDENCE_WARMING"],
        mean_lead_to_bust_hours=72.0,
        recovery_probability_48h=0.15,
    ),
    FailureMotif(
        motif_id="MOTIF-CONVECTIVE-TRIGGER",
        motif_name="Unresolved Mesoscale Convective Trigger",
        hazard_family=HazardFamily.PRECIPITATION,
        description="Sub-grid thermodynamic instability (high CAPE + low CIN) triggers localized convective storms poorly resolved by hydrostatic or coarse grids.",
        archetypal_trajectory=[0.05, 0.70, 0.90, 0.40, 0.20],
        precursor_signals=["ELEVATED_CAPE", "LOW_LEVEL_MOISTURE_CONVERGENCE", "STEEP_LAPSE_RATES", "BOUNDARY_LAYER_SHEAR"],
        mean_lead_to_bust_hours=36.0,
        recovery_probability_48h=0.45,
    ),
    FailureMotif(
        motif_id="MOTIF-TROUGH-PHASING",
        motif_name="Mid-Latitude Trough Phasing with Tropical Moisture",
        hazard_family=HazardFamily.WESTERN_DISTURBANCE,
        description="Deep upper-level mid-latitude westerly trough interacts with Arabian Sea moisture plume, generating massive orographic precipitation over Western Himalayas.",
        archetypal_trajectory=[0.15, 0.35, 0.80, 0.95, 0.70],
        precursor_signals=["DEEP_Z500_TROUGH", "SUBTROPICAL_JET_ACCELERATION", "ARABIAN_SEA_MOISTURE_PLUME", "OROGRAPHIC_LIFT"],
        mean_lead_to_bust_hours=60.0,
        recovery_probability_48h=0.25,
    ),
    FailureMotif(
        motif_id="MOTIF-TC-RECURVATURE",
        motif_name="Subtropical Ridge Track Recurvature Bifurcation",
        hazard_family=HazardFamily.CYCLONE,
        description="Tropical cyclone approaches Western flank of subtropical ridge; ensemble members split between westward continuation and sharp northeastward recurvature.",
        archetypal_trajectory=[0.10, 0.30, 0.75, 0.95, 0.90],
        precursor_signals=["SUBTROPICAL_RIDGE_WEAKENING", "MID_LATITUDE_TROUGH_APPROACH", "BIMODAL_ENSEMBLE_TRACK", "VERTICAL_SHEAR_GRADIENT"],
        mean_lead_to_bust_hours=84.0,
        recovery_probability_48h=0.10,
    ),
    FailureMotif(
        motif_id="MOTIF-DEPRESSION-SLOW",
        motif_name="Stalled Monsoon Low Pressure System Deluge",
        hazard_family=HazardFamily.MONSOON_LPS,
        description="Monsoon depression slows down or stalls over central/peninsular India, converting normal rainfall into catastrophic multi-day localized flooding.",
        archetypal_trajectory=[0.20, 0.40, 0.70, 0.90, 0.85],
        precursor_signals=["LOW_STEERING_FLOW", "HIGH_VORTICITY_850", "PRECIPITABLE_WATER_EXCESS", "MONSOON_TROUGH_OSCILLATION"],
        mean_lead_to_bust_hours=72.0,
        recovery_probability_48h=0.30,
    ),
    FailureMotif(
        motif_id="MOTIF-SQUALL-GUST",
        motif_name="Convective Downdraft Gale Squall",
        hazard_family=HazardFamily.SEVERE_WIND,
        description="Intense evaporatively cooled downdraft (microburst/macroburst) strikes the surface, producing localized gale-force gusts unrepresented in grid-mean winds.",
        archetypal_trajectory=[0.05, 0.85, 0.40, 0.20, 0.10],
        precursor_signals=["HIGH_DCAPE", "DRY_SUB_CLOUD_LAYER", "RAPID_PRESSURE_JUMP", "RADAR_REFLECTIVITY_BOW"],
        mean_lead_to_bust_hours=24.0,
        recovery_probability_48h=0.60,
    ),
]


class MotifClassifier:
    """Classifies forecast error trajectories and precursor signals against canonical motifs."""

    def __init__(self, motifs: Optional[List[FailureMotif]] = None):
        self.motifs = motifs or CANONICAL_FAILURE_MOTIFS

    def classify(
        self,
        trajectory: List[float],
        precursor_signals: List[str],
        hazard_family: Optional[HazardFamily | str] = None,
        min_similarity: float = 0.50,
    ) -> List[MotifMatchResult]:
        """Classify trajectory and signals, returning ranked motif match results."""
        if not trajectory:
            return []

        hazard_str = (
            hazard_family.value
            if isinstance(hazard_family, HazardFamily)
            else (str(hazard_family).upper() if hazard_family else None)
        )

        traj_arr = np.array(trajectory, dtype=np.float64)
        traj_norm = np.linalg.norm(traj_arr)
        if traj_norm > 1e-9:
            traj_unit = traj_arr / traj_norm
        else:
            traj_unit = traj_arr

        results: List[MotifMatchResult] = []
        signals_set = set(precursor_signals)

        for motif in self.motifs:
            # Filter by hazard if requested
            if hazard_str and motif.hazard_family.value != hazard_str:
                continue

            arch_arr = np.array(motif.archetypal_trajectory, dtype=np.float64)
            # Align dimensionality
            min_len = min(len(traj_unit), len(arch_arr))
            v1 = traj_unit[:min_len]
            v2 = arch_arr[:min_len]
            v2_norm = np.linalg.norm(v2)
            if v2_norm > 1e-9:
                v2_unit = v2 / v2_norm
            else:
                v2_unit = v2

            # Trajectory cosine similarity
            dot = float(np.dot(v1, v2_unit))
            traj_sim = max(0.0, min(1.0, (dot + 1.0) / 2.0))

            # Precursor match ratio
            matched_precursors = [p for p in motif.precursor_signals if p in signals_set]
            precursor_ratio = (
                len(matched_precursors) / len(motif.precursor_signals)
                if motif.precursor_signals
                else 0.0
            )

            # Combined similarity: 60% trajectory shape, 40% precursor physics
            combined_sim = 0.60 * traj_sim + 0.40 * precursor_ratio

            if combined_sim >= min_similarity:
                narrative = (
                    f"Trajectory matches {motif.motif_name} ({combined_sim:.1%} similarity) "
                    f"with {len(matched_precursors)}/{len(motif.precursor_signals)} precursor signals confirmed."
                )
                results.append(
                    MotifMatchResult(
                        motif_id=motif.motif_id,
                        motif_name=motif.motif_name,
                        hazard_family=motif.hazard_family,
                        similarity_score=round(combined_sim, 4),
                        precursors_matched=matched_precursors,
                        matched_precursor_ratio=round(precursor_ratio, 4),
                        narrative=narrative,
                    )
                )

        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results
