# Veyra roadmap — drop-in phase files

Follow **Phase A through Phase L in order**. Each phase file is self-contained. No external reference file is required to understand or execute a phase.

## Current strict status

The product has **2 substantial**, **12 partial**, **31 missing**, and **0 strictly proven end-to-end** capabilities out of 45 blueprint capabilities. The existing prototype-surface estimate is 66.7%, but the stricter scientific completion result is 0% proven until the V3 artifacts, canonical data, benchmark, and tests are reproducible.

## Global rule

Do not start the next phase until the current phase has:

- all listed commands executed;
- zero command errors;
- zero failed tests;
- a completed phase report;
- a recorded commit and push.

The exact push sequence is included at the end of every phase file. If the test fails, do not push.

## Phase order

1. [Phase A — Protect the foundation](PHASE_A_PROTECT_THE_FOUNDATION.md)
2. [Phase B — Scientific benchmark ladder](PHASE_B_SCIENTIFIC_BENCHMARK_LADDER.md)
3. [Phase C — Failure Memory](PHASE_C_FAILURE_MEMORY.md)
4. [Phase D — Failure dynamics](PHASE_D_FAILURE_DYNAMICS__MOTIFS__HAZARD_AND_RECOVERY.md)
5. [Phase E — Atmospheric intelligence](PHASE_E_ATMOSPHERIC_INTELLIGENCE.md)
6. [Phase F — Ensemble intelligence](PHASE_F_ENSEMBLE_INTELLIGENCE.md)
7. [Phase G — Spatial intelligence](PHASE_G_SPATIAL_INTELLIGENCE.md)
8. [Phase H — Safety and self-audit](PHASE_H_SAFETY_AND_SELF_AUDIT.md)
9. [Phase I — Statistical governance](PHASE_I_STATISTICAL_GOVERNANCE.md)
10. [Phase J — Multi-system intelligence](PHASE_J_MULTI_SYSTEM_INTELLIGENCE.md)
11. [Phase K — Independent truth challenge](PHASE_K_INDEPENDENT_TRUTH_CHALLENGE.md)
12. [Phase L — Frontier intelligence and digital twin](PHASE_L_FRONTIER_INTELLIGENCE_AND_DIGITAL_TWIN.md)

## Global safety rules

Never convert a plan or target into an achieved result. Never claim universal conditional coverage. Never use future truth, future calibration, future cycles, future model versions, future analogs, or nearby truth as issue-time features. Label synthetic outputs. Keep advanced models shadow-only until they beat the frozen baseline under the same split, target, reference, leakage rules, and bootstrap evaluation.

## Final product state

The target state machine is: `STABLE → WATCHING → DEGRADING → FAILURE_PRONE → ABSTAIN or BUST → RECOVERING → STABLE`.

The final system must expose one auditable reliability object containing forecast identity, probability, continuous error, miscoverage, hazard, recovery, memory, motifs, atmospheric and ensemble state, spatial propagation, fragility, margin, OOD, drift, calibration/reference health, abstention, decision mode, evidence and provenance.
