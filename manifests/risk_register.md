# Veyra Round-2 Scientific & Engineering Risk Register

## Identity & Scope
- **Document:** `manifests/risk_register.md`
- **Assessment Date:** 2026-09-22
- **Governance Framework:** Veyra 10 Non-Negotiable Integration Rules

---

| Risk ID | Category | Risk Description | Severity | Mitigation Strategy | Status |
|---|---|---|---|---|---|
| **R-001** | Artifact Integrity | V3 feature hash mismatch between codebase and release manifest (`265cffbb...`) | CRITICAL | Repaired in Phase 3 by regenerating authoritative schema from exact 50-feature baseline. | **RESOLVED** |
| **R-002** | Scientific Claims | Unvalidated deterministic formulas claimed as "certified ML specialists" | HIGH | Quarantined in Phase 6. All 6 specialists cataloged as `FORMULA_BASELINE` with Gate G8 promotion blocker. | **RESOLVED** |
| **R-003** | Scientific Integrity | Synthetic digital twin cycles masquerading as real historical observations | HIGH | Hard isolation in Phase 5: `/v1/revision` enforces immutable inputs, UI labels `SYNTHETIC` explicitly. | **RESOLVED** |
| **R-004** | Data Provenance | Real-time NCMRWF/NEPS Indian operational feed unavailable | MEDIUM | Explicitly disclosed as `FUTURE_BY_DESIGN` empirical program. Open-Meteo declared as public proxy. | **ACCEPTED** |
| **R-005** | Environment | Scikit-learn / LightGBM version mismatch warning during model unpickling | MEDIUM | Environment dependencies pinned in `requirements.txt`. Exact parity verified with max diff 0.00000000. | **RESOLVED** |
| **R-006** | CI Governance | Frontend-only GitHub Actions workflow without backend artifact or test gates | HIGH | Replaced with full `ci.yml` running 888 backend tests, artifact validator, vitest, and release gates. | **RESOLVED** |
| **R-007** | Temporal Safety | Posterior leakage from future observation into issue-time features | HIGH | Enforced via `time_contract.py`: strict UTC parsing, explicit lead hour derivation, no future leakage. | **RESOLVED** |
| **R-008** | Codebase Duplication | Redundant competing trees (`Builder-2`, `Parinidhi`, `Frontend-Original`) causing drift | HIGH | Trees inventoried in Phase 0, quarantined, and excluded from canonical import allowlists. | **RESOLVED** |
| **R-009** | Reliability Abstention | Fragile system failing silently or returning fake 0% bust probabilities | HIGH | Enforced safe abstention policy (`ABSTAIN`) with explicit diagnostic reasoning across all endpoints. | **RESOLVED** |
| **R-010** | Release Governance | Inability to revert failed deployment in under 5 minutes | MEDIUM | Documented `rollback_procedure.md` and tagged immutable release baselines (`v3.0.0-rc1`). | **RESOLVED** |
