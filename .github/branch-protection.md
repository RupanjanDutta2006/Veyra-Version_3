# Veyra Repository B — Branch Protection & Integration Rules

1. **Target Branch:** `integration/sih-round2-selective-merge` is the active staging integration branch.
2. **Upstream Main:** Never push unchecked experimental code or unverified artifacts to `main`.
3. **Selective Merge Only:** Imports from Repository A must strictly adhere to `manifests/import_allowlist.csv`.
4. **Denylist Enforcement:** Files listed in `manifests/import_denylist.csv` are strictly forbidden.
5. **No Duplicate Trees:** No secondary application trees (e.g. `Builder-2`, `Parinidhi`) allowed.
6. **Compulsory Gates:** Every integration phase must pass its gate test before proceeding.
