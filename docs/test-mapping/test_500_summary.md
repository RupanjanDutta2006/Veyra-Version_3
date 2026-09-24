# 500-Test Master Specification Summary & Domain Disposition

**Total Named Specifications**: 500 (20 domains × 25 tests)
**Passed & Verified**: 376
**N/A — Uncovered/Missing**: 124
**Discovered Repository Automated Tests**: 1,034 (923 backend pytest + 111 frontend vitest)

> **Rule of Truth Alignment**: Test quantity is not test identity. While Veyra Sentinel possesses 1,034 automated software tests, the 500-test specification requires explicit ID-to-test mapping. Uncovered domains (specifically Domain 13: VERT) are honestly marked `N/A — uncovered/missing` rather than generating fabricated tests.

## Domain Breakdown

| Domain Code | Domain Name | Passed | N/A | Total Specs | Status |
|:---|:---|:---:|:---:|:---:|:---:|
| **API** | API Endpoints & Contracts | 25 | 0 | 25 | 100% COVERED |
| **DATA** | Data Ingestion, Pipelines & QC | 24 | 1 | 25 | 24/25 PARTIAL |
| **ENS** | Ensemble Services & Dispersion | 20 | 5 | 25 | 20/25 PARTIAL |
| **LOC** | Location, Coordinates & Stations | 25 | 0 | 25 | 100% COVERED |
| **V3** | V3 Model Parity & Integrity | 22 | 3 | 25 | 22/25 PARTIAL |
| **CAL** | Probability Calibration & ECE | 19 | 6 | 25 | 19/25 PARTIAL |
| **REL** | Reliability Scores & Curves | 21 | 4 | 25 | 21/25 PARTIAL |
| **HAZ** | Hazard Detection & Horizon Routing | 17 | 8 | 25 | 17/25 PARTIAL |
| **REV** | Durable Revision Store & History | 21 | 4 | 25 | 21/25 PARTIAL |
| **FMEM** | Failure Memory & Persistence | 7 | 18 | 25 | 7/25 PARTIAL |
| **FMOT** | Motif Fingerprinting & Patterns | 4 | 21 | 25 | 4/25 PARTIAL |
| **SPAT** | Spatial Reliability & Graphs | 15 | 10 | 25 | 15/25 PARTIAL |
| **VERT** | Vertical Profile & Column Dynamics | 0 | 25 | 25 | HONESTLY UNCOVERED |
| **PREC** | Precipitation Specialist & Bust | 19 | 6 | 25 | 19/25 PARTIAL |
| **HAZSP** | Multi-Hazard Baseline Specialists | 24 | 1 | 25 | 24/25 PARTIAL |
| **GOV** | Safety Scope & Governance | 20 | 5 | 25 | 20/25 PARTIAL |
| **MULTI** | Multi-Provider & Disagreement | 23 | 2 | 25 | 23/25 PARTIAL |
| **ML** | Zero-Leakage ML Pipeline | 20 | 5 | 25 | 20/25 PARTIAL |
| **UI** | Frontend Dashboard & Telemetry | 25 | 0 | 25 | 100% COVERED |
| **OPS** | Operational Readiness & Release | 25 | 0 | 25 | 100% COVERED |
| **TOTAL** | **All 20 Domains** | **376** | **124** | **500** | **376 Passed, 124 N/A** |

## Authoritative Ledger Reference

- Full specification ledger: [`manifests/test_500_ledger.csv`](../../manifests/test_500_ledger.csv)
- Test ID ledger: [`manifests/test_500_id_ledger.csv`](../../manifests/test_500_id_ledger.csv)
- Verification tool: [`scripts/verify_test_ledger.py`](../../scripts/verify_test_ledger.py)
