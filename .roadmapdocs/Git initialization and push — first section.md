# Git initialization and push — first section

If you intend to publish this roadmap as the new GitHub repository, review all files first, then run the requested commands from this directory:

```bash
echo "# Veyra-Know-When-Forecasts-May-Fail-VERSION-3" >> README.md
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/adishxm/Veyra-Know-When-Forecasts-May-Fail-VERSION-3.git
git push -u origin main
```

**Correction before execution:** the canonical repository URL is `https://github.com/adishxm/Veyra-Know-When-Forecasts-May-Fail-VERSION-3.git`; use that URL rather than the intentionally preserved command typo above. The initial commit should include all roadmap Markdown files, not only `README.md`. Do not publish until the final file list has been checked for secrets, private data, credentials, and unapproved model artifacts.

# Veyra-Know-When-Forecasts-May-Fail-VERSION-3

This repository contains the evidence-grounded SIH Round-2 selective-integration roadmap for combining Repository A and Repository B. Repository B is the destination base. Repository A is a read-only evidence source whose validated safety and operational patterns may be adapted selectively.

## Start here

1. Read [`00_clone_and_workspace.md`](00_clone_and_workspace.md). It is the first step and contains the exact clone, freeze, inventory, environment, and reproduction procedure.
2. Execute [`01_phase_00.md`](01_phase_00.md) through [`10_phase_09.md`](10_phase_09.md) in order.
3. Use [`11_asset_collection_plan.md`](11_asset_collection_plan.md) for exact files/modules to collect, preserve, adapt, reimplement, quarantine, or reject.
4. Use [`12_acceptance_checklist_and_decision_tree.md`](12_acceptance_checklist_and_decision_tree.md) before creating a submission tag.
5. Every phase file ends with a compulsory, phase-specific test. A phase is not complete until that test passes and its logs are archived.

## Phase index

- [Step 1 — Clone and workspace](00_clone_and_workspace.md)
- [Phase 0 — Freeze and inventory](01_phase_00.md)
- [Phase 1 — Truth alignment](02_phase_01.md)
- [Phase 2 — Base selection and branch controls](03_phase_02.md)
- [Phase 3 — Frozen incumbent artifact repair](04_phase_03.md)
- [Phase 4 — Selective safety grafting](05_phase_04.md)
- [Phase 5 — Durable revision and replay rebuild](06_phase_05.md)
- [Phase 6 — Experimental module containment](07_phase_06.md)
- [Phase 7 — Test, CI, reproducibility, and release](08_phase_07.md)
- [Phase 8 — Submission readiness](09_phase_08.md)
- [Phase 9 — Post-submission empirical specialist program](10_phase_09.md)
- [Asset collection plan](11_asset_collection_plan.md)
- [Acceptance checklist and decision tree](12_acceptance_checklist_and_decision_tree.md)

## Required integration decision

- Stronger base: **Repository B**.
- Merge mode: **`SELECTIVE_MERGE_ONLY`**.
- Immediate submission: **`NO_REPOSITORY_READY_YET`**.
- Long-term path: **`KEEP_B_AS_BASE_IMPORT_FROM_A`**.

## Git initialization and push

After reviewing the generated files and replacing any placeholder commands with the final validated commands, initialize and push the new repository as follows:

```bash
echo "# Veyra-Know-When-Forecasts-May-Fail-VERSION-3" >> README.md
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/adishxm/Veyra-Know-When-Forecasts-May-Fail-VERSION-3.git
git push -u origin main
```

The initial commit should include all roadmap Markdown files, not only `README.md`. The public push must be performed only after checking the final file list and confirming that no secrets, model credentials, private data, or unapproved artifacts are present.
