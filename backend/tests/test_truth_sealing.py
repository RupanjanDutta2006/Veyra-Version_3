import pytest
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum

class SealState(str, Enum):
    UNSEALED = "UNSEALED"
    SEALED = "SEALED"

class TruthState(str, Enum):
    PENDING = "PENDING"
    AVAILABLE = "AVAILABLE"

@dataclass
class SealedRevisionRecord:
    revision_id: str
    issue_utc: str
    valid_utc: str
    feature_snapshot: Dict[str, Any]
    sealing_state: SealState = SealState.UNSEALED
    truth_availability: TruthState = TruthState.PENDING
    observed_truth: Optional[float] = None
    sealed_at: Optional[str] = None

    def seal(self):
        if self.sealing_state == SealState.SEALED:
            raise ValueError("Record is already sealed")
        self.sealing_state = SealState.SEALED
        self.sealed_at = datetime.now(timezone.utc).isoformat()

    def attach_truth(self, observed_value: float):
        if self.sealing_state != SealState.SEALED:
            raise ValueError("Cannot attach truth to unsealed issue-cycle record")
        self.observed_truth = observed_value
        self.truth_availability = TruthState.AVAILABLE

def test_truth_sealing_invariants():
    # 1. Issue time feature snapshot created
    features = {"t2m_fcst": 300.5, "lead_hours": 24, "cape": 1200.0}
    rec = SealedRevisionRecord(
        revision_id="rev_001",
        issue_utc="2026-09-22T00:00:00Z",
        valid_utc="2026-09-23T00:00:00Z",
        feature_snapshot=dict(features)
    )
    assert rec.sealing_state == SealState.UNSEALED
    assert rec.truth_availability == TruthState.PENDING

    # 2. Record must be sealed before truth arrives
    with pytest.raises(ValueError, match="unsealed"):
        rec.attach_truth(301.2)

    # 3. Seal at issue time
    rec.seal()
    assert rec.sealing_state == SealState.SEALED
    assert rec.sealed_at is not None

    # 4. Attach truth at valid time
    rec.attach_truth(301.2)
    assert rec.observed_truth == 301.2
    assert rec.truth_availability == TruthState.AVAILABLE

    # 5. Invariant: Original feature snapshot is completely unmodified
    assert rec.feature_snapshot == features
    assert "observed_truth" not in rec.feature_snapshot
