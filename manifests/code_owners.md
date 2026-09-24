# Veyra Code Ownership Map

| Path Pattern | Owner Role | Primary Responsibility |
|---|---|---|
| `models/v3/` | Model Custodian | Artifact integrity, SHA256 hashes, feature contracts |
| `backend/app/safety/` | Safety Architect | OOD detector, safe-fail abstention, trust boundaries |
| `backend/app/core/` | System Architect | Time contracts, UTC enforcement, certification policies |
| `backend/app/data/` | Data Engineer | Zarr store, SQLite revision history, truth sealing |
| `backend/app/api/` | Backend Lead | OpenAPI routes, response schemas, versioning |
| `backend/app/builder2/` | ML Engineer | Model adapters, feature pipelines, heuristic engines |
| `frontend/src/` | Frontend Lead | User interface, provenance badges, trust banners |
| `backend/tests/` | QA & Release Lead | Test suites, regression verification, replay harness |
| `manifests/` | Release Engineer | Release manifests, audit trails, claim registers |
| `docs/` | Documentation Lead | Evidence-class alignment, honest scientific language |
