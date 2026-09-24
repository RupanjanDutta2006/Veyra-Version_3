# Veyra Sentinel 500-Test Architecture & Mapping

This directory contains documentation, summaries, and audit ledgers for the 500-test master specification suite.

## Documents

- [`test_500_summary.md`](test_500_summary.md): Domain-by-domain disposition table across all 20 domains.
- [`../../manifests/test_500_ledger.csv`](../../manifests/test_500_ledger.csv): Authoritative 500-row CSV ledger.

## Verification

Run the automated ledger validator from repository root:
```bash
python scripts/verify_test_ledger.py
```
