# Phase 2 — Base selection and branch controls

## Objective

Establish Repository B as the sole destination and prevent a monolithic merge.

## Inputs from Repository A

Only the selected pattern list:

- safe model-unavailable behavior;
- UTC and issue-time contract;
- certification-scope boundaries;
- provider/fixture disclosure;
- revision-store semantics;
- replay invariants;
- selected safety and release tests.

Do not import Repository A’s application trees wholesale.

## Inputs from Repository B

- Current `backend/app` and versioned routes.
- Current `frontend/src`.
- Current model services and registries.
- Current `.github/workflows/deploy.yml`.
- Current test and lock files.

## Step-by-step work

1. Create a protected integration branch from Repository B.
2. Require pull requests and required checks for the integration branch.
3. Define the canonical destination directories.
4. Define a no-duplicate policy for backend, frontend, model, data, and deployment trees.
5. Create an import allowlist from Tables K and L.
6. Create an import denylist for pointer artifacts, duplicate trees, unverified metrics, synthetic outputs presented as live, and stale claims.
7. Define module ownership and code owners for model registry, safety, data history, API, UI, tests, and documentation.
8. Establish a single dependency lock and a single Python/Node build path.
9. Add a merge-check that rejects files copied outside the allowlist without an owner and validation plan.

## Outputs

- Protected integration branch.
- Canonical directory map.
- Import allowlist/denylist.
- Module ownership map.
- Initial Repository B-based branch.

## Failure conditions

- A second app tree is introduced.
- Repository A’s historical trees are copied without disposition.
- Model-serving code is copied into multiple competing paths.
- The branch can deploy without required checks.

## Gate P0-2

The destination must have one backend, one frontend, one model registry, one release manifest location, and one route-to-model authority.

## Compulsory test for Phase 2 — one destination and branch control

Run the destination-structure test:

```bash
set -euo pipefail
test "$(git branch --show-current)" = "integration/sih-round2-selective-merge"
test -d backend/app
test -d frontend/src
! find . -maxdepth 2 -type d \( -name 'Builder-2' -o -name 'Parinidhi' -o -name 'Frontend-Original' -o -name 'Overview' \) -print | grep -q .
find . -path '*/models/v3/*' -type f | sort
```

**Pass condition:** Repository B is the only application destination, no historical application tree has been imported, and the integration branch is cleanly identified.
