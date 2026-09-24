# Implementation Plan — Phase 5: Durable Revision Store and Honest Replay Rebuild

## Objective

Build one durable history and replay layer that can distinguish real historical replay from synthetic demonstration. Consolidate A's revision semantics with B's data history modules into one canonical service.

## Entry Criteria

- [ ] Phase 4 complete: safety patterns ported, V3 parity confirmed
- [ ] UTC/issue-time contract operational in B
- [ ] Provider identity and data-mode disclosure working

## Inputs

### From Repository A
| Module | Purpose |
|---|---|
| `backend/app/core/time_contract.py` | UTC safety |
| `revision_store.py` | Revision record design |
| `backend/app/services/revision_service.py` | Revision service API |
| SQLite/WAL exact-target design | Storage pattern reference |
| `backend/app/core/replay_harness.py` | Replay orchestration |
| `golden_replay_matrix.py` | Replay invariant testing |
| Replay and revision tests | Test intent |

### From Repository B
| Module | Purpose |
|---|---|
| `backend/app/data/zarr_store.py` | Zarr-based data store |
| Revision feature services | Feature version management |
| `failure_memory.py` | Episode-based failure learning |
| `failure_motifs.py` | Failure pattern detection |
| `independent_truth_audit.py` | Truth verification |
| `replay_digital_twin.py` | Synthetic replay simulation |
| Existing history and motif data | Historical episode data |

## Implementation Steps

### Step 5.1 — Define Canonical Revision Record

```python
@dataclass
class RevisionRecord:
    revision_id: str                  # Unique revision identifier
    issue_utc: datetime               # When prediction was issued
    valid_utc: datetime               # When prediction is valid for
    provider_id: str                  # Data provider identity
    forecast_version: str             # Which model version produced this
    target_id: str                    # What location/target
    feature_snapshot: Dict[str, Any]  # Frozen features at issue time
    truth_availability: TruthState    # available / pending / sealed
    calibration_state: str            # Which calibration was applied
    sealing_state: SealState          # unsealed / sealed / locked
    data_mode: DataMode               # live / cached / fixture / synthetic
    created_at: datetime              # Record creation timestamp
```

### Step 5.2 — Choose One Durable Store Contract

**Decision required:** Repository A uses SQLite/WAL, Repository B uses Zarr. Pick ONE.

| Criterion | SQLite/WAL (A) | Zarr (B) |
|---|---|---|
| ACID transactions | Yes | No |
| Exact-target lookup | Natural (SQL) | Requires index |
| Restart durability | Strong (WAL) | Depends on backend |
| Time-series optimization | Moderate | Strong |
| Deployment simplicity | High (file-based) | Moderate |

**Recommendation:** Choose based on the production deployment target. Document the decision and do NOT retain both as competing authorities.

### Step 5.3 — Define Exact-Target Lookup and Idempotency

```python
class RevisionKey:
    """Unique key for a revision record. Used for idempotency."""
    target_id: str
    issue_utc: datetime
    valid_utc: datetime
    provider_id: str
    forecast_version: str
    
    def to_idempotency_key(self) -> str:
        """Returns a hash-based key to prevent duplicate records."""
        ...
```

### Step 5.4 — Define Truth-Sealing Rules

**Critical rule:** Future truth cannot alter an already-issued feature snapshot.

```python
class TruthSealingPolicy:
    """
    Once a feature snapshot is sealed at issue time, truth arriving later
    can be recorded alongside but CANNOT modify the original features.
    """
    
    def seal_record(self, record: RevisionRecord) -> RevisionRecord:
        """Seal a record - no further modification to feature_snapshot allowed."""
        assert record.sealing_state == SealState.UNSEALED
        record.sealing_state = SealState.SEALED
        record.sealed_at = datetime.utcnow()
        return record
    
    def attach_truth(self, record: RevisionRecord, truth: TruthData) -> RevisionRecord:
        """Attach truth without modifying the original features."""
        assert record.sealing_state == SealState.SEALED
        record.truth_data = truth
        record.truth_availability = TruthState.AVAILABLE
        # feature_snapshot is UNCHANGED
        return record
```

### Step 5.5 — Implement Restart/Reload Tests

Create `backend/tests/test_revision_store_restart.py`:

- Write records → stop service → restart → verify records survive
- Write records across multiple issue cycles → verify temporal ordering
- Verify exact-target lookup returns correct records after restart

### Step 5.6 — Separate Synthetic from Historical Replay

**At every level — code, API, UI, storage:**

| Mode | Source Data | Label | Storage Prefix | API Field |
|---|---|---|---|---|
| Historical | Immutable real forecasts + independent truth | `HISTORICAL` | `history/` | `data_mode: "historical"` |
| Synthetic | Digital-twin generated cycles | `SYNTHETIC` | `synthetic/` | `data_mode: "synthetic"` |
| Fixture | Test fixtures | `FIXTURE` | `fixture/` | `data_mode: "fixture"` |

### Step 5.7 — Reject Fabricated History

In historical replay mode:
- REQUIRE immutable forecast inputs (cannot be generated)
- REQUIRE independent truth inputs (cannot be self-referential)
- REJECT synthetic progression as historical
- REJECT fabricated history records

### Step 5.8 — Port A Replay Invariants

From A's `replay_harness.py` and `golden_replay_matrix.py`:
- Replay must produce same results for same inputs
- Replay cannot introduce data not available at original issue time
- Replay metrics must state their data source mode

### Step 5.9 — Port B History Modules Selectively

From B's `failure_memory.py` and `failure_motifs.py`:
- Rebuild on sealed episode records (not raw/mutable data)
- Episode must have sealed feature snapshot + sealed truth
- Motif detection must use holdout episodes for validation

### Step 5.10 — Rebuild Failure Memory on Sealed Episodes

```python
class SealedFailureMemory:
    """Failure Memory that only consumes sealed revision records."""
    
    def ingest(self, episode: RevisionRecord):
        assert episode.sealing_state == SealState.SEALED
        assert episode.truth_availability == TruthState.AVAILABLE
        # Now safe to learn from this episode
        ...
```

### Step 5.11 — Ensure Replay Metrics Consistency

Every replay metric must declare:
- Its data source mode (historical / synthetic / fixture)
- Whether truth was available at issue time or attached later
- Whether features used live or cached data

## Outputs Checklist

- [ ] Canonical durable revision service (one store, one contract)
- [ ] Exact-target lookup and restart test suite
- [ ] Historical replay mode (immutable inputs, independent truth)
- [ ] Clearly labeled synthetic/fixture mode
- [ ] Sealed Failure Memory and Motif input contract
- [ ] Replay provenance ledger
- [ ] Truth-sealing enforcement

## Failure Conditions — Immediate Stop If:

| Condition | Why |
|---|---|
| Restart loses records | Durability failure |
| Provider or UTC identity missing from records | Lost provenance |
| Truth available before declared latency | Temporal violation |
| Synthetic cycles appear as historical observations | Scientific fraud |
| Replay metrics conflict with their source rows | Inconsistent evidence |

## Gates G9 and G11

| Gate | Requirement |
|---|---|
| **G9 Revision durability** | Records survive restart, preserve exact target/provider/time identity, seal truth correctly |
| **G11 Replay** | Historical mode uses immutable forecasts and independent truth; synthetic mode is visibly separate |

## Compulsory Gate Test

```bash
set -euo pipefail
pytest -q backend/tests/test_revision_store_restart.py \
  backend/tests/test_truth_sealing.py \
  backend/tests/test_replay_modes.py
python scripts/replay_historical.py \
  --mode historical \
  --fixtures artifacts/immutable_forecast_truth_fixture
python scripts/replay_digital_twin.py \
  --mode synthetic \
  --fixtures artifacts/synthetic_twin_fixture
```

**Pass condition:** Exact-target records survive restart, truth is sealed only at declared latency, historical mode uses immutable forecast/truth inputs, and synthetic mode is visibly separate.

---

**Previous:** [Phase 4 — Safety Grafting](06_phase4_safety_grafting.md)  
**Next:** [Phase 6 — Specialist Containment](08_phase6_specialist_containment.md)
