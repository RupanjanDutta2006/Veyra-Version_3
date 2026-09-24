# Veyra hazard-first roadmap — drop-in phase files

Follow **Phase A through Phase L in order**. This version reframes the entire plan using the attached SIH26079 research compilation, the Extraordinary Reliability Intelligence Blueprint, the Hazard-Specific Reliability Implementation Blueprint, and the repository audit. Each phase file is self-contained and includes its commands, completion gate, report format and zero-error Git push rule.

## Strict current status

The repository remains a V3 bust-risk prototype: 2 substantial capabilities, 12 partial/adjacent capabilities, 31 missing blueprint capabilities, and 0 strictly proven end-to-end. The prototype-surface score must not be confused with scientific certification.

## Exact hazard-first order

| Phase | Blueprint gate | Scope | Output |
|---|---|---|---|
| A | Gate 0 | V3 certification and hazard data contracts | V3_CERTIFIED |
| B | Gate 1 | ReliabilityState, Failure Memory, benchmark ladder | RELIABILITY_CORE_V1 |
| C | Gate 2 | Hazard curves, motifs, recovery and abstention | HAZARD_ENGINE_V1 |
| D | Gate 3 / P0 | Precipitation reliability | PRECIP_RELIABILITY_V1 |
| E | Gate 4 / P1 | Tropical cyclone reliability | CYCLONE_RELIABILITY_V1 |
| F | Gate 5 / P1 | Monsoon and low-pressure-system reliability | MONSOON_RELIABILITY_V1 |
| G | Gate 6 / P1 | Western disturbance reliability | WD_RELIABILITY_V1 |
| H | Gate 7 / P1 + P2 | Heatwave and data-dependent severe wind | HEATWAVE_RELIABILITY_V1 |
| I | Gate 8 | Spatial, compound and common-mode reliability | SPATIAL_RELIABILITY_V1 |
| J | Gate 9 | Hazard calibration, OOD, drift and independent truth | INDEPENDENT_TRUTH_AUDIT |
| K | Gate 10 | Cross-system transfer, operations and promotion | CROSS_SYSTEM_EVIDENCE |
| L | Gate 11 | Frontier challengers and digital twin | FRONTIER_CHALLENGER_REPORT |

## Non-negotiable execution rules

1. V3 is the incumbent until a challenger proves incremental value under the same target, temporal protocol, reference, leakage rules and bootstrap evaluation.
2. Hazard is not automatically a bust: cyclone, rain, heat, wind or OOD must be modelled as forecast-failure conditional on the hazard/regime.
3. Every hazard keeps its own targets: precipitation occurrence/amount/timing/placement; cyclone track/intensity/landfall; monsoon system/rainfall/transition; western-disturbance arrival/track/rain; heatwave threshold/timing/duration; wind threshold/timing/placement.
4. Every specialist publishes the same baseline table: climatology, spread, logistic/statistical, V3, V3 plus hazard, specialist and advanced challenger.
5. Every specialist runs the same ablation matrix: base, spread, revision, atmospheric, vertical, terrain, regime, memory, motifs, hazard features and full.
6. Every specialist reports temporal, geographic, seasonal, severity, OOD and reference slices with event counts and cycle-block bootstrap intervals.
7. Flood probability is not inferred from rainfall reliability. Compound hazards use explicit hazard sets, not unexplained averaged probabilities.
8. Experimental, diagnostic, operational-only, abstained, rejected and future outputs must never silently appear as certified science.
9. If any phase command fails or any test has a failure, do not push and do not start the next phase.

## Embedded detailed blueprint

[Open the hazard-specific implementation blueprint](VEYRA_Hazard_Specific_Reliability_Implementation_Blueprint.md) for the complete specialist target definitions, features, gates, benchmark tables, validation matrix, operational contract, promotion rules, rollback rules and first post-V3 agent task.

## Phase files

- [Phase A — V3 certification and hazard data contracts](PHASE_A_V3_CERTIFICATION_AND_HAZARD_DATA_CONTRACTS.md)
- [Phase B — Reliability core and benchmark ladder](PHASE_B_RELIABILITY_CORE_AND_BENCHMARK_LADDER.md)
- [Phase C — Multi-horizon hazard, motifs and recovery](PHASE_C_MULTI_HORIZON_HAZARD__MOTIFS_AND_RECOVERY.md)
- [Phase D — Precipitation reliability specialist](PHASE_D_PRECIPITATION_RELIABILITY_SPECIALIST.md)
- [Phase E — Tropical cyclone reliability specialist](PHASE_E_TROPICAL_CYCLONE_RELIABILITY_SPECIALIST.md)
- [Phase F — Monsoon and low-pressure-system reliability](PHASE_F_MONSOON_AND_LOW_PRESSURE_SYSTEM_RELIABILITY.md)
- [Phase G — Western disturbance reliability](PHASE_G_WESTERN_DISTURBANCE_RELIABILITY.md)
- [Phase H — Heatwave and data-dependent severe-wind specialists](PHASE_H_HEATWAVE_AND_DATA_DEPENDENT_SEVERE_WIND_SPECIALISTS.md)
- [Phase I — Spatial, compound and common-mode reliability](PHASE_I_SPATIAL__COMPOUND_AND_COMMON_MODE_RELIABILITY.md)
- [Phase J — Hazard-specific calibration, OOD, drift and independent truth](PHASE_J_HAZARD_SPECIFIC_CALIBRATION__OOD__DRIFT_AND_INDEPENDENT_TRUTH.md)
- [Phase K — Cross-system transfer, operations and promotion](PHASE_K_CROSS_SYSTEM_TRANSFER__OPERATIONS_AND_PROMOTION.md)
- [Phase L — Frontier challengers and reliability digital twin](PHASE_L_FRONTIER_CHALLENGERS_AND_RELIABILITY_DIGITAL_TWIN.md)

## Final user-facing reliability surface

The product should answer: will the forecast fail, where, when, why, what kind of failure, how sure is Veyra, whether the condition is OOD/abstained, and whether reliability recovers. The output dimension is `LOCATION × VARIABLE × LEAD × HAZARD × REGIME`, with evidence and provenance attached.

## Final state machine

`STABLE → WATCHING → DEGRADING → FAILURE_PRONE → ABSTAIN or BUST → RECOVERING → STABLE`.
