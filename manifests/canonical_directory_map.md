# Canonical Directory Mapping — Single Active Base (Repository B)

```text
backend/
├── app/
│   ├── api/            ← Versioned routes (SINGULAR authority: /v1)
│   ├── builder2/       ← Model adapter, feature pipeline (SINGULAR)
│   ├── core/           ← Core config, logging, time contract, certification policy
│   ├── data/           ← Zarr store, SQLite revision DB (SINGULAR)
│   ├── safety/         ← OOD detector, safe-fail abstention policy
│   └── services/       ← Forecasting & reliability services
├── tests/              ← All backend tests (Pytest)
frontend/
├── src/                ← React + Vite frontend application (SINGULAR)
models/
├── v3/                 ← V3 incumbent LightGBM & Isotonic calibrator (SINGULAR)
scripts/                ← Verification, test, and release automation scripts
manifests/              ← Authoritative ledgers, claim registers, release manifests
docs/                   ← Cleaned documentation & scientific guides
data/                   ← Operational topologies, reference benchmarks
```
