"""Authoritative Replay Modes & Provenance Governance for Veyra Round 2.

Enforces strict separation between physical historical ground-truth replay and
synthetic digital-twin simulation scenarios to prevent scientific conflation.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class ReplayMode(str, Enum):
    """Authoritative Replay Modes."""
    HISTORICAL = "historical"
    SYNTHETIC = "synthetic"
    FIXTURE = "fixture"


@dataclass
class ReplayContract:
    """Scientific contract and provenance metadata for replay execution."""
    mode: ReplayMode
    provenance: str
    is_synthetic: bool
    is_independent_truth: bool
    scenario_id: Optional[str] = None
    disclosure_notice: Optional[str] = None
    immutable_fixture_hash: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        self.validate()

    def validate(self) -> None:
        """Validate invariant rules governing replay mode separation."""
        if isinstance(self.mode, str):
            try:
                self.mode = ReplayMode(self.mode)
            except ValueError:
                raise ValueError(f"Invalid replay mode: '{self.mode}'. Must be one of {[m.value for m in ReplayMode]}")

        # Invariant 1: Historical mode CANNOT be synthetic and MUST represent independent truth
        if self.mode == ReplayMode.HISTORICAL:
            if self.is_synthetic:
                raise ValueError(
                    "Scientific Conflation Violation: Historical replay records CANNOT have is_synthetic=True. "
                    "Synthetic simulation outputs must not masquerade as historical atmospheric reality."
                )
            if not self.is_independent_truth:
                raise ValueError(
                    "Scientific Truth Violation: Historical replay records MUST be backed by independent ground truth."
                )

        # Invariant 2: Synthetic mode MUST be flagged as synthetic and CANNOT claim independent truth
        elif self.mode == ReplayMode.SYNTHETIC:
            if not self.is_synthetic:
                raise ValueError(
                    "Provenance Violation: Synthetic digital-twin records MUST have is_synthetic=True."
                )
            if self.is_independent_truth:
                raise ValueError(
                    "Scientific Representation Violation: Synthetic simulation data CANNOT claim to be independent ground truth."
                )
            if not self.disclosure_notice:
                self.disclosure_notice = "[NOTICE] Operating in explicit SYNTHETIC demonstration mode."

        # Invariant 3: Fixture mode must declare whether it represents synthetic or historical fixtures
        elif self.mode == ReplayMode.FIXTURE:
            if self.is_synthetic and self.is_independent_truth:
                raise ValueError(
                    "Contradictory Provenance: Fixture record cannot simultaneously be synthetic and independent ground truth."
                )

    def to_dict(self) -> Dict[str, Any]:
        """Convert replay contract to dictionary."""
        return {
            "mode": self.mode.value,
            "provenance": self.provenance,
            "is_synthetic": self.is_synthetic,
            "is_independent_truth": self.is_independent_truth,
            "scenario_id": self.scenario_id,
            "disclosure_notice": self.disclosure_notice,
            "immutable_fixture_hash": self.immutable_fixture_hash,
            "created_at": self.created_at,
        }


def create_historical_replay_record(
    provenance: str = "NOAA GEFSv12 / IMD AWS Historical Observation Reanalysis",
    scenario_id: Optional[str] = None,
    immutable_fixture_hash: Optional[str] = None,
) -> ReplayContract:
    """Create a verified historical replay contract record."""
    return ReplayContract(
        mode=ReplayMode.HISTORICAL,
        provenance=provenance,
        is_synthetic=False,
        is_independent_truth=True,
        scenario_id=scenario_id,
        immutable_fixture_hash=immutable_fixture_hash,
    )


def create_synthetic_replay_record(
    provenance: str = "Reliability Digital Twin Scenario Generator (Simulated Atmospheric Stress)",
    scenario_id: Optional[str] = None,
    disclosure_notice: str = "[NOTICE] Operating in explicit SYNTHETIC demonstration mode.",
) -> ReplayContract:
    """Create an explicitly disclosed synthetic digital-twin replay record."""
    return ReplayContract(
        mode=ReplayMode.SYNTHETIC,
        provenance=provenance,
        is_synthetic=True,
        is_independent_truth=False,
        scenario_id=scenario_id,
        disclosure_notice=disclosure_notice,
    )
