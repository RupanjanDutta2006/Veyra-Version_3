# VEYRA --- Hazard-Specific Forecast Reliability Implementation Blueprint

**Version:** 1.0\
**Scope:** Post-Extraordinary implementation\
**SIH:** 26079 --- AI-Based Forecast Bust Detection for Medium-Range
Weather Forecasts

> **North star:** Veyra does not replace an issued weather forecast. It
> estimates when, where, under what atmospheric conditions, and for
> which hazard that forecast is likely to become unreliable --- and when
> Veyra itself should abstain.

------------------------------------------------------------------------

# 1. How this document fits the Veyra program

This document is the **implementation layer** between the existing plans
and actual engineering.

-   **Extraordinary Blueprint:** defines the scientific vision ---
    Failure Memory, Failure Motifs, Predictability Geometry,
    Hazard/Recovery, Spatial Failure, Vertical Intelligence, OOD, Drift,
    independent validation and frontier challengers.
-   **Phase 3 Roadmap:** defines production discipline ---
    certification, adapters, registry, watchlists, alerts,
    benchmark/champion-challenger, red-team and release freeze.
-   **This document:** defines how to implement those ideas **hazard by
    hazard**.

The execution pattern is always:

``` text
Research evidence
      ↓
Scientific question
      ↓
Target + reference contract
      ↓
Leakage audit
      ↓
Simple baseline
      ↓
V3 / hazard-feature challenger
      ↓
Advanced challenger only if justified
      ↓
Out-of-time + subgroup validation
      ↓
Calibration / OOD / robustness
      ↓
Promotion or rejection
```

------------------------------------------------------------------------

# 2. Non-negotiable rules

## 2.1 V3 is the incumbent

Do not replace the frozen V3 because a new architecture looks more
advanced.

Current authoritative benchmark:

  Metric                                                  V3
  ---------------------------------- -----------------------
  PR-AUC                                              0.2110
  Brier                                               0.0538
  Brier Skill Score                                  +0.0770
  ECE                                                 0.0068
  OOT rows                                           116,250
  Short / Medium / Extended PR-AUC     0.284 / 0.219 / 0.142
  Bust prevalence                                     \~6.2%

Every challenger uses the same target, temporal protocol, reference
definition, leakage rules and evaluation contract before comparison.

## 2.2 No future information

At issue time `t0`, inference may use only information available at
`t0`.

Forbidden:

-   future observations;
-   future reanalysis values;
-   future forecast errors;
-   future bust labels;
-   future radar/satellite frames;
-   post-valid-time corrections;
-   target-derived features.

Historical outcomes may be used offline for training and Failure Memory
only through issue-time-safe retrieval.

## 2.3 Hazard ≠ bust

A cyclone, heavy-rain event, heatwave, large ensemble spread or OOD
state is not automatically a forecast bust. The specialist estimates
**forecast failure conditional on the hazard/regime**.

## 2.4 Keep uncertainty concepts separate

Veyra must distinguish:

``` text
P(|forecast error| > operational threshold)
P(truth outside a forecast interval)
continuous forecast-error distribution
uncertainty in Veyra's own probability
OOD / unsupported-state score
```

------------------------------------------------------------------------

# 3. Target architecture

``` text
                  ISSUED FORECAST
                        │
       ┌────────────────┼────────────────┐
       │                │                │
    Ensemble        Atmosphere       Forecast
    members           state          revision
       │                │                │
       └────────────────┼────────────────┘
                        ↓
              COMMON FORECAST STATE
                        │
          ┌─────────────┼─────────────┐
          ↓             ↓             ↓
    Failure Memory  Failure Motifs  Ensemble Geometry
          │             │             │
          └─────────────┼─────────────┘
                        ↓
                HAZARD / REGIME
                   DETECTION
                        │
       ┌────────────────┼────────────────┐
       ↓                ↓                ↓
 Precipitation       Cyclone        Monsoon / LPS
       ↓                ↓                ↓
 Western Disturbance  Heatwave   Severe Wind / Others
       └────────────────┼────────────────┘
                        ↓
                RELIABILITY FUSION
                        ↓
       ┌────────────────┼────────────────┐
       ↓                ↓                ↓
    P(BUST)       Continuous error   Hazard failure
       │                              probabilities
       └────────────────┬───────────────┘
                        ↓
               MULTI-HORIZON HAZARD
                        ↓
             Time-to-bust / Recovery
                        ↓
                Spatial reliability
                        ↓
             OOD / Drift / Calibration
                        ↓
              Evidence + Decision Mode
                        ↓
                   Veyra UI/API
```

------------------------------------------------------------------------

# 4. Common `ReliabilityState` contract

All specialist engines should emit a compatible object:

``` python
ReliabilityState = {
    "forecast_identity": ..., "issue_time": ..., "location": ...,
    "variable": ..., "lead_hours": ..., "model_version": ...,
    "forecast_values": ..., "ensemble_summary": ...,
    "ensemble_geometry": ...,
    "bust_probability": ..., "continuous_error_distribution": ...,
    "hazard_type": ..., "hazard_probability": ...,
    "hazard_curve": ..., "survival_curve": ...,
    "expected_time_to_bust": ..., "expected_time_to_recovery": ...,
    "failure_memory": ..., "failure_motif": ...,
    "atmospheric_regime": ..., "vertical_regime": ...,
    "spatial_risk": ..., "propagation_score": ...,
    "ood_score": ..., "drift_score": ..., "missingness_score": ...,
    "calibration_health": ..., "reference_health": ...,
    "reliability_state": ..., "abstention_state": ...,
    "decision_mode": ..., "evidence": ..., "provenance": ...
}
```

This becomes the backbone for Builder 2 → Builder 1 integration.

------------------------------------------------------------------------

# 5. Universal experiment contract

Every new component gets an experiment record containing:

``` text
experiment_id
hazard
scientific_question
hypothesis
data_source
forecast_system
issue_time / valid_time
reference
label definition
threshold definition
feature families
leakage audit
temporal split
geographic split
baseline
challenger
primary metric
secondary metrics
calibration metrics
subgroup metrics
ablation plan
bootstrap method
success criterion
rollback criterion
artifact hash
code/data version
decision
```

## Baseline ladder

1.  Historical climatology
2.  Persistence / historical difficulty
3.  Raw ensemble spread
4.  Spread → bust logistic regression
5.  Compact statistical model
6.  Current V3
7.  V3 + hazard features
8.  Specialist LightGBM / probabilistic tree
9.  Sequence/spatial challenger
10. Advanced model only if the preceding level demonstrates an
    information gap

## Required evaluation

-   PR-AUC
-   Brier
-   Brier Skill Score
-   ECE / reliability diagrams
-   calibration intercept/slope where appropriate
-   CRPS for probabilistic continuous-error models
-   risk-coverage / selective performance
-   lead-wise performance
-   season-wise performance
-   location/geographic holdout
-   regime-wise performance
-   extreme-event slices
-   OOD slices
-   event/cycle-block bootstrap confidence intervals

------------------------------------------------------------------------

# 6. SHARED INTELLIGENCE LAYERS

## 6.1 Failure Memory

For each historical failure episode store:

``` text
failure_event_id
hazard
issue_time
location
lead
forecast system/version
forecast-state representation
ensemble summary
vertical summary
atmospheric regime
observed/reference error
bust label
severity
motif_id
reference provenance
```

Retrieval is:

``` text
current state
→ hazard filter
→ lead filter
→ season/regime filter
→ nearest historical states
→ historical failure frequency + support
```

Never show a historical rate without its sample count and uncertainty.

## 6.2 Failure Motifs

Candidate motifs are hypotheses, not truth:

``` text
RAPID ENSEMBLE DIVERGENCE
FALSE CONSENSUS
REGIME TRANSITION
REVISION CASCADE
EXTREME-TAIL BREAKDOWN
TERRAIN-COUPLED FAILURE
SPATIAL DISPLACEMENT
COMMON-MODE FAILURE
SLOW DEGRADATION
RECOVERY AFTER INSTABILITY
```

A motif is promoted only if it reproduces on held-out periods.

## 6.3 Predictability Geometry

If member-level GEFS data are available, compare summary statistics
against richer ensemble geometry:

-   covariance structure;
-   eigenvalues/effective dimension;
-   anisotropy;
-   member clustering;
-   pairwise distances;
-   spread growth;
-   divergence acceleration;
-   trajectory separation.

Experiment:

``` text
V3 + mean/spread/quantiles
vs
V3 + full member geometry
```

If geometry does not produce stable out-of-time gain, do not keep it.

## 6.4 Multi-horizon hazard

Do not treat ten lead predictions as unrelated numbers. Evaluate the
trajectory:

``` text
risk(+24), risk(+48), ... risk(+240)
```

and derive:

-   risk growth;
-   expected time-to-bust;
-   peak risk;
-   survival;
-   recovery probability.

## 6.5 OOD and selective prediction

Evaluate whether abstaining on unsupported states actually reduces risk:

``` text
coverage → residual risk
```

Report risk-coverage curves rather than treating OOD as a magic
probability.

------------------------------------------------------------------------

# 7. HAZARD 1 --- PRECIPITATION RELIABILITY ENGINE

## Priority: P0 / mandatory

Precipitation is explicitly relevant to the SIH problem statement and
must become a real benchmarked specialist, not a UI label.

## 7.1 Core question

> When is an issued precipitation forecast likely to fail in occurrence,
> amount, threshold, timing, accumulation or spatial placement?

## 7.2 Failure taxonomy

### A. Occurrence

``` text
forecast dry / observed wet
forecast wet / observed dry
```

### B. Amount

``` text
signed error
absolute error
threshold exceedance
error quantiles
```

### C. Heavy rainfall

Predict the probability that a declared heavy-rain threshold will be
missed or falsely predicted.

### D. Extreme rainfall

Separate the tail from ordinary precipitation. Report prevalence, event
count, Brier/BSS, reliability, POD, FAR, CSI/ETS where justified and
uncertainty intervals.

### E. Timing

``` text
forecast event/peak time vs observed/reference event/peak time
```

### F. Spatial displacement

A forecast can have the right amount but the wrong location. Consider
neighborhood/object/spatial metrics only when the data supports them.

### G. Accumulation window

Keep 6/12/24/48/72-hour accumulation targets distinct if the data
contract supports them.

## 7.3 Issue-time features

### Ensemble

-   mean/median
-   quantiles
-   spread
-   wet-member fraction
-   dry-member fraction
-   exceedance fraction
-   spread growth
-   ensemble clustering
-   forecast revision

### Atmosphere

-   temperature
-   humidity/moisture indicators
-   pressure
-   wind
-   vertical wind structure
-   shear
-   convergence proxies
-   upper-level flow

### Terrain/context

-   elevation
-   mountain/coastal/inland class
-   terrain proximity
-   season
-   monsoon regime

## 7.4 Research basis

### Evans et al. 2025 --- HRRR forecast-error prediction

Directly relevant because it predicts NWP forecast error for
temperature, wind and precipitation using sequence models and
observations as reference. Use its target/evaluation logic as
inspiration, not as a claim that HRRR results transfer automatically to
GEFS/India.

### Evans et al. 2026 --- LSTM + Vision Transformer forecast-error prediction

Relevant for combining temporal sequences with vertical atmospheric
information. It motivates a Veyra challenger with richer atmospheric
context after simple models are established.

### India / GEFS precipitation postprocessing literature

Use this to understand GEFS precipitation behavior over India,
regional/seasonal difficulty and appropriate precipitation
reference/evaluation design.

### Angus et al. 2024 --- heavy precipitation over India

Useful for comparing probabilistic postprocessing ideas such as quantile
mapping and EMOS and for evaluating exceedance probabilities. Veyra's
task remains different: **diagnose forecast reliability**, not merely
correct the forecast.

## 7.5 Exact model progression

``` text
P0.1 target specification
P0.2 data/reference audit
P0.3 climatology baseline
P0.4 raw ensemble baseline
P0.5 spread → bust logistic
P0.6 V3 + precipitation features
P0.7 continuous-error distribution
P0.8 heavy-rain specialist
P0.9 sequence challenger
P0.10 spatial challenger
P0.11 reference/independent-observation challenge
P0.12 calibration + OOD
P0.13 integration
```

## 7.6 Output

``` json
{
  "hazard": "PRECIPITATION",
  "occurrence_failure_probability": null,
  "amount_failure_probability": null,
  "heavy_rain_failure_probability": null,
  "extreme_rain_failure_probability": null,
  "timing_failure_probability": null,
  "spatial_displacement_probability": null,
  "overall_reliability": null,
  "evidence": [],
  "ood": null,
  "provenance": {}
}
```

Unsupported quantities must be `null`, never invented.

------------------------------------------------------------------------

# 8. HAZARD 2 --- TROPICAL CYCLONE RELIABILITY ENGINE

## Priority: P1

Cyclone reliability must be decomposed into track, intensity, timing and
landfall failure.

## 8.1 Targets

-   track-error threshold exceedance;
-   intensity error;
-   rapid-intensification failure;
-   landfall-location error;
-   landfall-timing error;
-   track uncertainty.

Keep targets separate rather than creating one opaque cyclone score.

## 8.2 Features

### Track

-   forecast position and motion;
-   ensemble track spread;
-   track clustering;
-   steering flow;
-   environmental wind;
-   moisture;
-   vertical shear;
-   forecast-cycle revision.

### Intensity

-   pressure tendency;
-   wind/intensity ensemble disagreement;
-   moisture;
-   shear;
-   upper-level environment;
-   ocean/environmental information only when available in the frozen
    live contract.

## 8.3 Research basis

**Fernandez et al. 2025**, probabilistic tropical-cyclone track-error
prediction, provides a direct example of situation-dependent
probabilistic forecast-error modelling.

**Meng & Song 2024**, conformal cyclone-track uncertainty, is relevant
to uncertainty regions and coverage.

**Tsai et al. 2026**, situation-dependent cyclone uncertainty, motivates
trajectory-aware sequence modelling.

Veyra should use these as methodological inputs while preserving its own
forecast-failure objective.

## 8.4 Model progression

``` text
historical track difficulty
→ ensemble track spread
→ spread logistic
→ V3 + cyclone features
→ probabilistic track-error challenger
→ sequence challenger
→ conformal uncertainty challenger
→ OOT validation
```

------------------------------------------------------------------------

# 9. HAZARD 3 --- MONSOON / LOW-PRESSURE-SYSTEM RELIABILITY

## Priority: P1

Cover separately:

-   low-pressure systems;
-   depressions;
-   deep depressions;
-   monsoon depressions;
-   active monsoon regimes;
-   break monsoon regimes.

## 9.1 Failure questions

1.  Is system location likely to be wrong?
2.  Is propagation speed likely to be wrong?
3.  Is rainfall placement likely to be wrong?
4.  Is rainfall intensity likely to be wrong?
5.  Is system deepening likely to be wrong?
6.  Is the active/break regime unstable?
7.  Is a regime transition likely to invalidate the current forecast?

## 9.2 Features

-   sea-level pressure;
-   pressure tendency;
-   circulation;
-   850-hPa circulation/wind;
-   700/500-hPa flow;
-   moisture transport;
-   precipitation ensemble structure;
-   track and propagation speed;
-   vertical shear;
-   historical analogue states.

## 9.3 Research basis

Use ensemble/lagged monsoon-depression studies, WRF sensitivity studies,
regional background-error work and recent attention-based rainfall
modelling around monsoon depressions to design targets and feature
families.

The engineering conclusion is:

``` text
Monsoon reliability
= system dynamics reliability
+ precipitation reliability
+ regime-transition reliability
```

Do not collapse these into one untestable score.

------------------------------------------------------------------------

# 10. HAZARD 4 --- WESTERN DISTURBANCE RELIABILITY

## Priority: P1

## 10.1 Failure modes

-   arrival-time failure;
-   track/position failure;
-   precipitation amount failure;
-   precipitation displacement;
-   duration/intensity failure;
-   rain/snow partition failure only if suitable observations exist.

## 10.2 Atmospheric features

-   250/300-hPa jet structure;
-   upper-level trough;
-   500-hPa geopotential pattern;
-   moisture transport;
-   low-level pressure/wind;
-   vertical shear;
-   terrain/elevation;
-   temperature profile;
-   forecast revision.

## 10.3 Build sequence

``` text
WD event catalogue
→ regime detector
→ historical error statistics
→ failure motifs
→ specialist model
→ terrain-conditioned validation
→ OOT integration
```

Do not build a WD model before confirming that event labels and
reference data are reproducible.

------------------------------------------------------------------------

# 11. HAZARD 5 --- HEATWAVE RELIABILITY

## Priority: P1

Heatwave failure is primarily a persistence/threshold problem.

## 11.1 Targets

-   threshold miss;
-   peak-temperature error;
-   onset timing error;
-   cessation timing error;
-   duration error;
-   spatial-extent error;
-   persistence failure;
-   nighttime-temperature failure where supported.

## 11.2 Features

-   2-m temperature;
-   ensemble mean/spread;
-   anomaly from climatology;
-   persistence;
-   pressure;
-   wind;
-   humidity;
-   land/soil variables where available;
-   forecast revision;
-   regime/blocking indicators where justified;
-   terrain/coastal/urban class.

## 11.3 Model progression

``` text
climatology
→ ensemble baseline
→ threshold logistic
→ V3 + persistence/regime features
→ specialist LightGBM
→ temporal challenger
→ OOT / geographic validation
```

------------------------------------------------------------------------

# 12. HAZARD 6 --- SEVERE / HIGH-WIND RELIABILITY

## Priority: P2, data-dependent

Targets:

-   maximum-wind error;
-   threshold exceedance failure;
-   timing failure;
-   spatial placement failure.

Features:

-   ensemble wind distribution;
-   pressure gradient;
-   vertical wind profile;
-   shear;
-   frontal/synoptic regime;
-   terrain;
-   forecast revision.

This module is activated only if paired forecast/reference data can
produce defensible labels.

------------------------------------------------------------------------

# 13. EXTREME RAIN / FLOOD-RELEVANT EXTENSION

Do not claim flood prediction from rainfall reliability alone.

Safe first scope:

``` text
extreme-rainfall forecast reliability
```

A true flood model requires additional hydrology, basin, drainage,
runoff, soil and observational data.

Therefore:

``` text
Veyra rainfall failure risk ≠ flood probability
```

A future hydrological extension can be evaluated separately.

------------------------------------------------------------------------

# 14. COMPOUND HAZARDS

## Advanced

Real events can overlap:

``` text
cyclone + extreme rain + high wind
western disturbance + moisture surge + mountain precipitation
```

Represent the hazard set explicitly rather than averaging probabilities:

``` text
hazard_set = {
  precipitation: ...,
  cyclone: ...,
  wind: ...
}
```

Possible future methods:

-   multi-task learning;
-   calibrated joint models;
-   dependence/coupling models;
-   graph-based dependence.

Do not pursue compound modelling until the individual modules are
trustworthy.

------------------------------------------------------------------------

# 15. COMMON-MODE FAILURE

A dangerous situation is:

``` text
ensemble spread low
BUT
all members share the same wrong physical evolution
```

This can produce a "confidently wrong" forecast.

Experiment:

``` text
spread-only
vs
spread + historical/regime-conditioned common-mode indicators
```

Candidate evidence:

-   persistent systematic error;
-   regime-conditioned bias;
-   shared model-version signature;
-   initialization mismatch;
-   recurring residual structure.

Do not call this causal without evidence.

------------------------------------------------------------------------

# 16. SPATIAL FAILURE PROPAGATION

Once location-level specialists are validated, treat the 25 canonical
locations as a network.

``` text
nodes = locations
edges = learned lagged forecast-failure dependence
```

Question:

> Does elevated failure risk at one location provide information about
> later risk elsewhere, after controlling for common atmospheric
> factors?

Call the result a **forecast-failure propagation relationship**, not
causality.

Research basis includes work on spatially coherent forecast-error
structures and spatial probabilistic postprocessing.

------------------------------------------------------------------------

# 17. VERTICAL ATMOSPHERIC INTELLIGENCE

For precipitation, cyclones, monsoon systems and western disturbances,
surface variables alone may be insufficient.

Potential pressure levels:

``` text
850 hPa
700 hPa
500 hPa
300 hPa
250 hPa
```

Potential features:

-   humidity profiles;
-   wind profiles;
-   shear;
-   lapse rates;
-   moisture gradients;
-   instability proxies;
-   jet structure;
-   PBL indicators.

Evans et al. 2026 provides a direct research motivation for combining
temporal information with vertical atmospheric context in forecast-error
prediction.

The implementation must still benchmark whether these features add value
to Veyra's GEFS task.

------------------------------------------------------------------------

# 18. CALIBRATION AND OOD BY HAZARD

Global calibration can hide specialist failure.

For each hazard report:

``` text
global
lead
season
location
regime
severity
OOD
reference
```

Metrics:

-   Brier/BSS;
-   ECE;
-   reliability diagrams;
-   calibration slope/intercept where appropriate;
-   conditional coverage where appropriate;
-   risk-coverage.

Use the conditional-coverage/conformal literature as methodological
guidance, but never claim universal conditional coverage without proving
the assumptions.

------------------------------------------------------------------------

# 19. INDEPENDENT-TRUTH CHALLENGE

Current historical verification is heavily reference-based. Later,
compare:

``` text
GEFS → ERA5 reference
```

against:

``` text
GEFS → independent station / radiosonde / satellite / GNSS evidence
```

where legitimate, paired and sufficiently complete data exist.

The objective is **reference sensitivity analysis**, not declaring one
source universally correct.

------------------------------------------------------------------------

# 20. MODEL COMPLEXITY LADDER

Never jump directly to a Transformer/diffusion model.

``` text
L0 climatology
L1 ensemble spread
L2 logistic/statistical
L3 LightGBM
L4 V3 + hazard features
L5 temporal sequence model
L6 spatial/graph model
L7 vertical + spatial model
L8 foundation-model representation
L9 generative spatial reliability field
```

Each level must prove incremental value.

------------------------------------------------------------------------

# 21. FRONTIER CHALLENGER TRACK

Only after the core is scientifically stable, test representations from
accessible AI-weather systems such as:

-   GenCast;
-   NeuralGCM;
-   AIFS;
-   Aurora;
-   other reproducible foundation-model outputs.

Use them as challengers/features, not automatic replacements.

Possible frontier spatial model:

``` text
P(BUST at x,y | forecast state)
```

Potential methods:

-   graph models;
-   spatial transformers;
-   conditional diffusion;
-   probabilistic spatial fields.

CoDiCast and related conditional probabilistic weather work can inform
this track.

------------------------------------------------------------------------

# 22. BENCHMARK TABLE FOR EVERY HAZARD

Every specialist must publish a table like:

  Model                   PR-AUC   Brier   BSS   ECE   Risk@coverage OOT
  --------------------- -------- ------- ----- ----- --------------- -----
  Climatology                                                        
  Spread                                                             
  Logistic                                                           
  V3                                                                 
  V3 + hazard                                                        
  Specialist                                                         
  Advanced challenger                                                

Also report lead, season, geography, regime, severity, OOD and reference
slices.

------------------------------------------------------------------------

# 23. REQUIRED ABLATION MATRIX

For each specialist:

``` text
BASE
BASE + spread
BASE + revision
BASE + atmospheric
BASE + vertical
BASE + terrain
BASE + regime
BASE + failure memory
BASE + motifs
BASE + hazard-specific features
FULL
```

This is essential because "full model improved" does not tell us why.

------------------------------------------------------------------------

# 24. VALIDATION MATRIX

## Temporal

Use future untouched periods. Avoid random row splits for overlapping
weather windows.

## Geographic

-   seen locations;
-   unseen locations where sample size allows;
-   regional holdout.

## Seasonal

At minimum:

``` text
winter
pre-monsoon
monsoon
post-monsoon
```

## Severity

``` text
ordinary
moderate
heavy
extreme
```

Always report event counts.

------------------------------------------------------------------------

# 25. OPERATIONAL CONTRACT

Every hazard module declares:

``` text
forecast provider
variable
units
grid/resolution
issue time
valid time
ensemble size
missingness
latency
reference
label definition
thresholds
version
```

No silent provider substitution. No hidden unit conversion.

Examples:

``` text
temperature: K ↔ °C explicitly
pressure: Pa ↔ hPa explicitly
wind: m/s ↔ km/h explicitly
precipitation: mm + declared accumulation interval
```

------------------------------------------------------------------------

# 26. USER-FACING RELIABILITY SURFACE

The final scientific object should approach:

``` text
LOCATION × VARIABLE × LEAD × HAZARD × REGIME
```

Example:

``` text
Kolkata
Precipitation
D+4
Monsoon Active

P(forecast failure): 0.63
Reliability: DEGRADING
OOD: Moderate
Evidence support: 12 historical analogues
```

The system should answer:

### Will the forecast fail?

`P(BUST)`

### Where?

Location/region.

### When?

Lead-time hazard curve.

### Why?

Atmospheric + ensemble + historical evidence.

### What kind of failure?

Amount, timing, track, intensity, threshold or spatial displacement.

### How sure is Veyra?

Calibration, OOD, support and fragility.

### Will it recover?

Recovery trajectory where validated.

------------------------------------------------------------------------

# 27. EXACT IMPLEMENTATION GATES

## Gate 0 --- V3 Certification

Before new model work:

-   recover authoritative V3 artifact;
-   verify model and calibrator hashes;
-   restore/locate benchmark dataset;
-   reconcile historical/live schema;
-   certify Builder 1 ↔ Builder 2 provenance;
-   rerun regression.

**Deliverable:** `V3_CERTIFIED`

## Gate 1 --- Reliability Core

Build:

-   Failure Memory schema;
-   episode builder;
-   retrieval API;
-   motif pipeline;
-   ReliabilityState;
-   evidence/provenance contract.

**Deliverable:** `RELIABILITY_CORE_V1`

## Gate 2 --- Hazard / Recovery

Build and test:

-   multi-horizon risk curve;
-   time-to-bust;
-   survival representation;
-   recovery state;
-   lead-wise calibration.

**Deliverable:** `HAZARD_ENGINE_V1`

## Gate 3 --- Precipitation

``` text
P0.1 target contract
P0.2 data audit
P0.3 climatology
P0.4 ensemble baseline
P0.5 spread logistic
P0.6 V3 + precipitation features
P0.7 continuous-error model
P0.8 heavy-rain specialist
P0.9 sequence challenger
P0.10 spatial challenger
P0.11 independent/reference challenge
P0.12 calibration/OOD
P0.13 integration
```

**Deliverable:** `PRECIP_RELIABILITY_V1`

## Gate 4 --- Cyclone

``` text
C1 event catalogue
C2 track targets
C3 intensity targets
C4 ensemble baseline
C5 V3 + cyclone features
C6 probabilistic track challenger
C7 conformal challenger
C8 timing/landfall
C9 OOT validation
C10 integration
```

**Deliverable:** `CYCLONE_RELIABILITY_V1`

## Gate 5 --- Monsoon/LPS

``` text
M1 regime/event catalogue
M2 track target
M3 precipitation target
M4 regime-transition target
M5 ensemble baseline
M6 specialist
M7 motifs
M8 OOT validation
M9 integration
```

**Deliverable:** `MONSOON_RELIABILITY_V1`

## Gate 6 --- Western Disturbance

``` text
W1 event catalogue
W2 regime detector
W3 track/timing targets
W4 precipitation target
W5 jet/vertical features
W6 terrain conditioning
W7 specialist
W8 OOT validation
W9 integration
```

**Deliverable:** `WD_RELIABILITY_V1`

## Gate 7 --- Heatwave

``` text
H1 event catalogue
H2 threshold target
H3 duration target
H4 onset/cessation target
H5 persistence features
H6 specialist
H7 OOT validation
H8 integration
```

**Deliverable:** `HEATWAVE_RELIABILITY_V1`

## Gate 8 --- Spatial Reliability

Only after trustworthy location-level specialists:

``` text
S1 location graph
S2 lagged dependence
S3 spatial clustering
S4 spatial calibration
S5 regional aggregation
S6 risk surface
S7 adversarial spatial tests
```

**Deliverable:** `SPATIAL_RELIABILITY_V1`

## Gate 9 --- Independent Truth

**Deliverable:** `INDEPENDENT_TRUTH_AUDIT`

## Gate 10 --- Cross-System Transfer

Train/test across aligned forecast systems where data permits.

**Deliverable:** `CROSS_SYSTEM_EVIDENCE`

## Gate 11 --- Frontier Challengers

Only now test foundation representations, advanced graph/attention and
generative spatial fields.

**Deliverable:** `FRONTIER_CHALLENGER_REPORT`

------------------------------------------------------------------------

# 28. PROMOTION / ROLLBACK RULE

A challenger is **not promoted** if it:

-   improves average skill but harms extreme-event slices;
-   improves PR-AUC but damages calibration;
-   works only on seen locations;
-   depends on unavailable live data;
-   uses leakage;
-   cannot reproduce;
-   has unstable output;
-   adds substantial complexity without measurable value.

In all such cases:

``` text
REJECT / ARCHIVE CHALLENGER
        ↓
KEEP CERTIFIED INCUMBENT
```

------------------------------------------------------------------------

# 29. FINAL STATUS TAXONOMY

Every repository capability must be labelled exactly one of:

-   `FROZEN` --- protected scientific baseline
-   `CERTIFIED` --- experimentally validated and approved
-   `EXPERIMENTAL` --- active challenger
-   `DIAGNOSTIC` --- informative but not decision-authoritative
-   `OPERATIONAL_ONLY` --- operationally exposed but not
    benchmark-certified
-   `ABSTAINED` --- insufficient evidence/data
-   `REJECTED` --- tested and not promoted
-   `FUTURE` --- designed but not implemented

Experimental output must never silently appear as certified science.

------------------------------------------------------------------------

# 30. RESEARCH INDEX

## Forecast-error prediction

-   Cahill et al. (2024), *Errors of Opportunity: Using Neural Networks
    to Predict Errors in GEFS on S2S Time Scales*.
-   Evans et al. (2025), *Predicting Forecast Error for the HRRR Using
    LSTM Neural Networks*, arXiv:2512.14898.
-   Evans et al. (2026), *A Hybrid LSTM--Vision Transformer Architecture
    for Predicting HRRR Forecast Errors*, arXiv:2606.19026.
-   AI2ES `forecast_error_hrrr` open implementation.

## Precipitation / India

-   *Improving short to medium range GEFS precipitation forecast in
    India*.
-   Angus et al. (2024), heavy-precipitation postprocessing over India,
    DOI:10.1002/qj.4677.
-   2026 work on ML postprocessing of precipitation ensemble forecasts
    over India.

## Uncertainty / calibration

-   Asch et al. (2026), rigorous UQ with conformal prediction,
    arXiv:2606.19642.
-   Gibbs, Cherian & Candès (2025), conditional conformal guarantees,
    DOI:10.1093/jrsssb/qkaf008.
-   Min, Peng & Zou (2026), unified theory of conditional coverage.
-   Braun et al. (2025), conditional coverage diagnostics.

## Cyclones

-   Fernandez et al. (2025), probabilistic tropical-cyclone track-error
    prediction, DOI:10.1175/AIES-D-24-0066.1.
-   Meng & Song (2024), conformal tropical-cyclone track uncertainty,
    DOI:10.1016/j.eswa.2024.123743.
-   Tsai et al. (2026), situation-dependent tropical-cyclone track
    uncertainty.

## Spatial / model error

-   Gupta et al. (2023), spatially coherent forecast-error structures,
    DOI:10.1002/qj.4536.
-   Bonavita & Laloyaux (2020), ML for model-error inference/correction,
    DOI:10.1029/2020MS002232.

## Frontier

-   GenCast;
-   NeuralGCM;
-   AIFS / AIFS-CRPS;
-   Aurora;
-   CoDiCast (IJCAI 2025) and related conditional probabilistic
    weather-field research.

These papers are **research inputs**, not evidence that Veyra's exact
GEFS/India benchmark is already solved.

------------------------------------------------------------------------

# 31. FIRST AGENT TASK AFTER V3 CERTIFICATION

Do **not** ask an agent to build the whole plan.

The first task is:

``` text
BUILD PRECIPITATION RELIABILITY EXPERIMENT CONTRACT ONLY.

Do not modify frozen V3.
Do not retrain production models.
Do not fabricate precipitation data.

Produce:
1. precipitation data availability audit
2. forecast/reference join specification
3. issue-time leakage audit
4. failure taxonomy
5. target definitions
6. threshold manifest
7. baseline experiment configuration
8. metrics configuration
9. provenance/artifact manifest
10. automated tests
11. report template

STOP after the audit.
Do not train until the data/target contract is reviewed and passes.
```

Then proceed one experiment at a time:

``` text
Precipitation climatology
→ raw ensemble
→ spread logistic
→ V3 + precip features
→ continuous error
→ heavy-rain specialist
→ sequence challenger
→ spatial challenger
→ independent truth
→ calibration/OOD
→ integration
```

------------------------------------------------------------------------

# 32. FINAL NORTH STAR

> **Veyra should become an evidence-backed forecast-reliability
> intelligence engine specialized in the atmospheric situations where
> existing forecasts are most likely to fail --- especially
> precipitation, cyclones, monsoon systems, western disturbances and
> heatwaves --- while continuously measuring when, where and why that
> reliability assessment itself should be trusted.**

The objective is not to win by having the largest model.

The objective is to win on **scientific depth, reproducibility, hazard
coverage, calibrated reliability, explainability, safe abstention, and
demonstrable incremental value**.
