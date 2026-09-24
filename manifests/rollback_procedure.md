# Veyra Round-2 Production Rollback and Incident Recovery Procedure

## Document Identity
- **Version:** 1.0.0
- **Scope:** Veyra Severe Weather Bust Prediction System (Round-2 Monorepo)
- **Target Branch:** `main` / `integration/sih-round2-selective-merge`
- **Release Baseline Tag:** `v3.0.0-rc1`

---

## 1. Rollback Triggers (Immediate Stop Conditions)
A rollback to the prior verified release state must be initiated immediately upon detection of any of the following:
1. **Artifact Checksum Drift (Gate G1/G3 Failure):**
   - Active V3 model or calibrator SHA256 does not match the authoritative release manifest (`00a84107...` and `9f448606...`).
2. **Prediction Parity Deviation (Gate G2 Failure):**
   - Absolute difference between candidate predictions and golden V3 baseline exceeds `1e-6`.
3. **Temporal Invariant Violation (Gate G4 Failure):**
   - Lead hour mismatch, issue-time posterior leakage, or missing UTC validation.
4. **Specialist Containment Breach (Gate G8 Failure):**
   - An unpromoted, formula-baseline, or experimental specialist modifies production `P(BUST)`.
5. **Revision Store Data Loss (Gate G9 Failure):**
   - Database corruption or unrecoverable restart data loss.
6. **False Mode Masquerading (Gate G11 Failure):**
   - Synthetic digital-twin cycles labeled as historical data.

---

## 2. Fast Rollback Procedure (Target MTTR < 5 Minutes)

### Step 1: Drain Incoming Traffic & Enable Fallback
If the live service is serving traffic via reverse proxy or container:
```bash
# Switch traffic to fallback safe response mode
export VEYRA_FORCE_ABSTENTION="true"
export VEYRA_ABSTENTION_REASON="System in rollback verification"
```

### Step 2: Rollback Git Deployment
Revert the active deployment to the last known good signed release tag (`v3.0.0-rc1` or previous stable commit):
```bash
git fetch --tags
git checkout tags/v3.0.0-rc1
```

### Step 3: Run Compulsory Artifact Integrity Gate
Verify that all incumbent artifacts are intact:
```bash
python scripts/verify_artifacts.py
```
*Expected output: Exit code 0, all SHA256 hashes match authoritative release manifest.*

### Step 4: Run Health and Smoke Checks
Verify that the rolled-back service starts cleanly:
```bash
python -m pytest backend/tests/test_scientific_certification.py -q
python -m pytest backend/tests/test_v3_time_contract.py -q
```

### Step 5: Resume Traffic
```bash
unset VEYRA_FORCE_ABSTENTION
unset VEYRA_ABSTENTION_REASON
```

---

## 3. Database & Revision Store Recovery
1. The durable revision store uses SQLite with Write-Ahead Logging (`WAL`).
2. In case of store corruption:
   - Check point state: `sqlite3 data/revision_store.db "PRAGMA integrity_check;"`
   - If corrupted, restore from the last hourly backup snapshot:
     ```bash
     cp backups/revision_store_latest.db data/revision_store.db
     ```
   - If backup is unavailable, clear corrupt journal files and allow store initialization to regenerate clean schema. Unrecorded history will safely fail to `INSUFFICIENT_HISTORY` without manufacturing synthetic records.

---

## 4. Post-Rollback Postmortem Requirements
Within 24 hours of rollback:
1. File an incident record in `docs/incidents/`.
2. Document root cause, triggered gate ID, and affected components.
3. Add a regression test preventing recurrence before reapplying changes.
