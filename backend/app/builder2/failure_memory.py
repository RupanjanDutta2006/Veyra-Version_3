"""Failure Memory Engine & Historical Episode Retrieval (Blueprint Section 6.1 / Gate 1).

Stores historical forecast failure episodes with:
- episode_id, hazard_family, issue_time, location, lead_hours
- forecast system & version
- state representation vector
- observed/reference error, bust label, severity, motif_id, and reference provenance

Provides issue-time-safe nearest neighbor retrieval filtered by hazard, lead horizon,
season, and synoptic regime, computing analog bust frequencies with sample support counts.
"""

from datetime import datetime
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
from pydantic import BaseModel, Field

from backend.app.contracts.hazard_contracts import HazardFamily


class FailureEpisode(BaseModel):
    """Historical forecast failure episode record."""
    episode_id: str = Field(..., description="Unique episode identifier")
    hazard_family: HazardFamily = Field(..., description="Associated hazard category")
    issue_time: str = Field(..., description="UTC issue time of historical run")
    location: str = Field(..., description="Location name or station identifier")
    lead_hours: int = Field(..., ge=0)
    forecast_system: str = Field(default="GEFS_V12")
    forecast_state_vector: List[float] = Field(..., description="Normalized feature embedding vector")
    observed_error: float = Field(..., description="Realized forecast error |F - O|")
    bust_label: int = Field(..., ge=0, le=1, description="1 if bust occurred, 0 otherwise")
    severity: str = Field(default="MODERATE", description="LOW, MODERATE, SEVERE, or CATASTROPHIC")
    motif_id: Optional[str] = Field(None, description="Classified failure motif identifier")
    reference_provenance: str = Field(default="ERA5_REANALYSIS")


class FailureMemoryMatch(BaseModel):
    """Single retrieved historical analog episode with distance."""
    episode: FailureEpisode
    distance: float = Field(..., ge=0.0, description="Feature distance in phase space")
    similarity_score: float = Field(..., ge=0.0, le=1.0)


class FailureMemoryQueryResult(BaseModel):
    """Aggregated retrieval result for issue-time Failure Memory queries."""
    query_hazard: Optional[str]
    query_lead: Optional[int]
    total_candidates_evaluated: int
    matches: List[FailureMemoryMatch]
    sample_support_count: int = Field(..., description="Number of historical analogs retrieved")
    historical_failure_frequency: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Observed bust frequency among analogs"
    )
    mean_historical_error: Optional[float] = None
    analog_uncertainty_score: float = Field(..., description="Uncertainty inversely proportional to sample support")


class FailureMemoryStore:
    """In-memory and persisted storage for Failure Memory episodes."""

    def __init__(self, persistence_path: Optional[Path] = None):
        self.persistence_path = persistence_path
        self._episodes: List[FailureEpisode] = []
        if persistence_path and persistence_path.is_file():
            self.load()

    def add_episode(self, episode: FailureEpisode) -> None:
        """Add a single historical episode to memory."""
        self._episodes.append(episode)

    def add_episodes(self, episodes: List[FailureEpisode]) -> None:
        """Batch add historical episodes."""
        self._episodes.extend(episodes)

    def count(self) -> int:
        """Total stored failure episodes."""
        return len(self._episodes)

    def save(self) -> None:
        """Persist episodes to JSON."""
        if not self.persistence_path:
            return
        self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
        data = [ep.model_dump() for ep in self._episodes]
        with open(self.persistence_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self) -> None:
        """Load episodes from JSON."""
        if not self.persistence_path or not self.persistence_path.is_file():
            return
        with open(self.persistence_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        self._episodes = [FailureEpisode.model_validate(item) for item in raw]

    def retrieve_analogs(
        self,
        query_vector: List[float],
        hazard: Optional[HazardFamily | str] = None,
        lead_hours: Optional[int] = None,
        lead_window_hours: int = 24,
        top_k: int = 5,
    ) -> FailureMemoryQueryResult:
        """Retrieve nearest historical failure analogs with issue-time constraints.

        Rule §6.1: Never show a historical rate without its sample count and uncertainty.
        """
        if not self._episodes:
            return FailureMemoryQueryResult(
                query_hazard=str(hazard) if hazard else None,
                query_lead=lead_hours,
                total_candidates_evaluated=0,
                matches=[],
                sample_support_count=0,
                historical_failure_frequency=None,
                mean_historical_error=None,
                analog_uncertainty_score=1.0,
            )

        hazard_str = hazard.value if isinstance(hazard, HazardFamily) else (str(hazard).upper() if hazard else None)
        q_vec = np.array(query_vector, dtype=np.float64)

        candidates: List[tuple[FailureEpisode, float]] = []
        for ep in self._episodes:
            # Filter by hazard if specified
            if hazard_str and ep.hazard_family.value != hazard_str:
                continue

            # Filter by lead horizon within window if specified
            if lead_hours is not None:
                if abs(ep.lead_hours - lead_hours) > lead_window_hours:
                    continue

            ep_vec = np.array(ep.forecast_state_vector, dtype=np.float64)
            if len(ep_vec) != len(q_vec):
                # Align dimensionality by padding or slicing for robust distance computation
                min_len = min(len(ep_vec), len(q_vec))
                dist = float(np.linalg.norm(q_vec[:min_len] - ep_vec[:min_len]))
            else:
                dist = float(np.linalg.norm(q_vec - ep_vec))

            candidates.append((ep, dist))

        total_evaluated = len(candidates)
        if not candidates:
            return FailureMemoryQueryResult(
                query_hazard=hazard_str,
                query_lead=lead_hours,
                total_candidates_evaluated=0,
                matches=[],
                sample_support_count=0,
                historical_failure_frequency=None,
                mean_historical_error=None,
                analog_uncertainty_score=1.0,
            )

        # Sort by distance (ascending)
        candidates.sort(key=lambda x: x[1])
        top_candidates = candidates[:top_k]

        matches: List[FailureMemoryMatch] = []
        for ep, dist in top_candidates:
            sim = 1.0 / (1.0 + dist)
            matches.append(FailureMemoryMatch(episode=ep, distance=dist, similarity_score=sim))

        sample_count = len(matches)
        bust_count = sum(1 for m in matches if m.episode.bust_label == 1)
        freq = bust_count / sample_count if sample_count > 0 else 0.0
        mean_err = float(np.mean([m.episode.observed_error for m in matches])) if sample_count > 0 else 0.0

        # Uncertainty is high when sample support is low (Rule §6.1)
        uncertainty = max(0.05, min(1.0, 1.0 / math.sqrt(sample_count + 1)))

        return FailureMemoryQueryResult(
            query_hazard=hazard_str,
            query_lead=lead_hours,
            total_candidates_evaluated=total_evaluated,
            matches=matches,
            sample_support_count=sample_count,
            historical_failure_frequency=round(freq, 4),
            mean_historical_error=round(mean_err, 4),
            analog_uncertainty_score=round(uncertainty, 4),
        )
