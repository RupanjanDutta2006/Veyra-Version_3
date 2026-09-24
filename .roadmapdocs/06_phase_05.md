# Phase 5 — Durable revision store and honest replay rebuild

## Objective

Build one durable history and replay layer that can distinguish real historical replay from synthetic demonstration.

## Inputs from Repository A

- `backend/app/core/time_contract.py`.
- `revision_store.py`.
- `backend/app/services/revision_service.py`.
- SQLite/WAL exact-target design.
- `backend/app/core/replay_harness.py`.
- `golden_replay_matrix.py`.
- Replay and revision tests.

## Inputs from Repository B

- `backend/app/data/zarr_store.py`.
- Revision feature services.
- `failure_memory.py`.
- `failure_motifs.py`.
- `independent_truth_audit.py`.
- `replay_digital_twin.py`.
- Existing history and motif data.

## Step-by-step work

1. Define the canonical revision record: issue UTC, valid UTC, provider ID, forecast version, target ID, feature snapshot, truth availability, calibration state, and sealing state.
2. Choose one durable store contract; do not retain SQLite/WAL and Zarr as competing authorities.
3. Define exact-target lookup and idempotency keys.
4. Define truth-sealing rules so future truth cannot alter an already-issued feature snapshot.
5. Implement restart/reload tests across multiple issue cycles.
6. Separate synthetic digital-twin cycles from historical replay at code, API, UI, and storage levels.
7. Reject fabricated history and synthetic progression in historical mode.
8. Require immutable forecast and independent truth inputs for historical replay.
9. Port A replay invariants and B history modules selectively into the canonical service.
10. Rebuild Failure Memory and Failure Motifs on sealed episode records.
11. Ensure replay metrics are internally consistent and state their data mode.

## Outputs

- Canonical durable revision service.
- Exact-target and restart test suite.
- Historical replay mode.
- Clearly labeled synthetic/fixture mode.
- Sealed Failure Memory and Motif input contract.
- Replay provenance ledger.

## Failure conditions

- Restart loses records.
- Provider or UTC identity is missing.
- Truth is available before the declared latency.
- Synthetic cycles appear as historical observations.
- Replay metrics conflict with their source rows.

## Gates G9 and G11

- **G9 Revision durability:** records survive restart, preserve exact target/provider/time identity, and seal truth correctly.
- **G11 Replay:** historical mode uses immutable forecasts and independent truth; synthetic mode is visibly separate.

## Compulsory test for Phase 5 — durable revision and replay separation

Run restart, truth-sealing, and replay-mode checks:

```bash
set -euo pipefail
pytest -q backend/tests/test_revision_store_restart.py backend/tests/test_truth_sealing.py backend/tests/test_replay_modes.py
python scripts/replay_historical.py --mode historical --fixtures artifacts/immutable_forecast_truth_fixture
python scripts/replay_digital_twin.py --mode synthetic --fixtures artifacts/synthetic_twin_fixture
```

**Pass condition:** exact-target records survive restart, truth is sealed only at the declared latency, historical mode uses immutable forecast/truth inputs, and synthetic mode is visibly separate.
