"""Unit Tests for Hazard-Specific Reliability Engines (Gate 3 / Phase D).

Verifies:
- PrecipitationReliabilitySpecialist baseline ladder progression
- Multi-component prediction (Occurrence, Amount, Heavy Rain, Extreme, Timing, Spatial)
- Strict null-safety on unsupported features
- Continuous error distribution estimation (CRPS)
- Out-of-Distribution (OOD) detection and selective prediction abstention
- Full integration with universal ReliabilityState schema
"""

import pytest

from backend.app.builder2.precipitation_specialist import PrecipitationReliabilitySpecialist
from backend.app.builder2.cyclone_specialist import CycloneReliabilitySpecialist
from backend.app.builder2.monsoon_specialist import MonsoonReliabilitySpecialist
from backend.app.builder2.western_disturbance_specialist import WesternDisturbanceReliabilitySpecialist
from backend.app.builder2.heatwave_specialist import HeatwaveReliabilitySpecialist
from backend.app.contracts.precipitation_contract import PrecipitationIssueFeatures
from backend.app.contracts.cyclone_contract import CycloneBasin, CycloneIssueFeatures
from backend.app.contracts.monsoon_contract import (
    MonsoonIssueFeatures,
    MonsoonRegimeState,
    MonsoonSystemType,
)
from backend.app.contracts.western_disturbance_contract import (
    WDIssueFeatures,
    WDIntensityClass,
    WDTerrainRegime,
    WDTroughTilt,
)
from backend.app.contracts.heatwave_contract import (
    HeatwaveIssueFeatures,
    HeatwaveRegime,
    HeatwaveSeverity,
)
from backend.app.schemas.reliability_state import (
    DecisionMode,
    OperationalReliabilityState,
    ReliabilityState,
)


@pytest.fixture
def specialist():
    return PrecipitationReliabilitySpecialist()


@pytest.fixture
def nominal_features():
    return PrecipitationIssueFeatures(
        lead_hours=48,
        ensemble_mean_precip_mm=22.0,
        ensemble_median_precip_mm=20.5,
        ensemble_spread_precip_mm=8.4,
        ensemble_p90_precip_mm=32.0,
        wet_member_fraction=0.80,
        dry_member_fraction=0.20,
        heavy_exceedance_fraction=0.10,
        cape_proxy_jkg=1800.0,
        precipitable_water_mm=52.0,
        low_level_moisture_convergence=0.03,
        orographic_lift_proxy=0.5,
        terrain_class="mountain",
    )


def test_climatology_baseline(specialist):
    """Test Level 1: Climatological baseline rates."""
    p_monsoon = specialist.evaluate_climatology_baseline(season="monsoon", terrain_class="inland")
    p_winter = specialist.evaluate_climatology_baseline(season="winter", terrain_class="inland")
    assert 0.0 < p_winter < p_monsoon < 1.0


def test_raw_ensemble_baseline(specialist):
    """Test Level 2: Raw ensemble spread uncertainty proxy."""
    p_low_spread = specialist.evaluate_raw_ensemble_baseline(spread_mm=2.0, mean_mm=20.0)
    p_high_spread = specialist.evaluate_raw_ensemble_baseline(spread_mm=25.0, mean_mm=20.0)
    assert p_high_spread > p_low_spread


def test_spread_logistic_baseline(specialist):
    """Test Level 3: Calibrated spread logistic regression."""
    p_short = specialist.evaluate_spread_logistic_baseline(spread_mm=10.0, lead_hours=24)
    p_long = specialist.evaluate_spread_logistic_baseline(spread_mm=10.0, lead_hours=120)
    assert p_long > p_short


def test_continuous_error_distribution(specialist):
    """Test Level 5: Continuous error distribution and CRPS estimation."""
    dist = specialist.evaluate_continuous_error_distribution(mean_mm=25.0, spread_mm=10.0, lead_hours=48)
    assert dist.rmse > 0.0
    assert dist.mae > 0.0
    assert dist.q10 <= dist.q50 <= dist.q90
    assert dist.crps is not None and dist.crps > 0.0


def test_predict_nominal(specialist, nominal_features):
    """Test comprehensive specialist prediction under nominal conditions."""
    out = specialist.predict(nominal_features, has_subdaily_data=True, has_spatial_radar=True)
    assert out.hazard == "PRECIPITATION"
    assert out.occurrence_failure_probability is not None
    assert out.amount_failure_probability is not None
    assert out.heavy_rain_failure_probability is not None
    assert out.timing_failure_probability is not None
    assert out.spatial_displacement_probability is not None
    assert out.overall_reliability is not None
    assert out.ood is False
    assert len(out.evidence) >= 3


def test_unsupported_fields_null(specialist, nominal_features):
    """Test that unsupported sub-daily timing and spatial radar inputs remain null."""
    out = specialist.predict(nominal_features, has_subdaily_data=False, has_spatial_radar=False)
    assert out.timing_failure_probability is None
    assert out.spatial_displacement_probability is None
    # Occurrence and amount are still evaluated
    assert out.occurrence_failure_probability is not None
    assert out.amount_failure_probability is not None


def test_ood_detection_and_abstention(specialist):
    """Test OOD detection and abstention state when inputs exceed physical support."""
    ood_features = PrecipitationIssueFeatures(
        lead_hours=72,
        ensemble_mean_precip_mm=120.0,
        ensemble_median_precip_mm=115.0,
        ensemble_spread_precip_mm=95.0,  # Exceeds ood_spread_threshold_mm (80.0)
        ensemble_p90_precip_mm=180.0,
        wet_member_fraction=0.90,
        dry_member_fraction=0.10,
        cape_proxy_jkg=5200.0,            # Extreme CAPE
        precipitable_water_mm=92.0,       # Extreme PWAT
        terrain_class="mountain",
    )

    out = specialist.predict(ood_features)
    assert out.ood is True
    assert float(out.provenance.get("ood_score", 0.0)) >= 0.70

    # Universal ReliabilityState integration under OOD
    state = specialist.to_reliability_state(ood_features)
    assert state.abstention_state is True
    assert state.decision_mode == DecisionMode.ABSTAIN_UNSUPPORTED
    assert state.reliability_state == OperationalReliabilityState.ABSTAIN
    assert state.bust_probability is None  # Must be null when abstaining


def test_to_reliability_state_integration(specialist, nominal_features):
    """Test full generation of universal 30-field ReliabilityState contract."""
    state = specialist.to_reliability_state(
        nominal_features,
        forecast_id="FCST-TEST-DELHI",
        location="DELHI",
    )
    assert isinstance(state, ReliabilityState)
    assert state.forecast_identity == "FCST-TEST-DELHI"
    assert state.hazard_type == "PRECIPITATION"
    assert state.bust_probability is not None
    assert len(state.hazard_curve) > 0
    assert len(state.survival_curve) == len(state.hazard_curve)

    # Invariant: Survival curve must be monotonically non-increasing
    for i in range(len(state.survival_curve) - 1):
        assert state.survival_curve[i+1] <= state.survival_curve[i]

    assert state.decision_mode == DecisionMode.NOMINAL
    assert state.reliability_state == OperationalReliabilityState.STABLE


# ==============================================================================
# Tropical Cyclone Reliability Specialist Tests (Gate 4 / Phase E)
# ==============================================================================

@pytest.fixture
def cyclone_specialist():
    return CycloneReliabilitySpecialist()


@pytest.fixture
def nominal_cyclone_landfall_features():
    return CycloneIssueFeatures(
        lead_hours=48,
        basin=CycloneBasin.BAY_OF_BENGAL,
        forecast_lat=18.5,
        forecast_lon=86.2,
        forward_speed_kmh=18.0,
        ensemble_track_spread_km=85.0,
        ensemble_track_clustering=0.25,
        forecast_max_wind_ms=45.0,
        ensemble_intensity_spread_ms=5.5,
        vertical_wind_shear_ms=12.0,
        steering_flow_speed_ms=6.5,
        steering_flow_dir_deg=315.0,
        central_pressure_tendency_hpa_12h=-10.0,
        distance_to_coast_km=140.0,
        forecast_landfall=True,
        forecast_landfall_lead_hours=54,
    )


def test_cyclone_baselines(cyclone_specialist):
    """Test Level 1, 2, 3 cyclone track baselines."""
    p_clim = cyclone_specialist.evaluate_climatology_baseline(basin=CycloneBasin.BAY_OF_BENGAL, lead_hours=48)
    assert 0.05 < p_clim < 0.50

    p_raw_low = cyclone_specialist.evaluate_raw_ensemble_baseline(track_spread_km=40.0, lead_hours=48)
    p_raw_high = cyclone_specialist.evaluate_raw_ensemble_baseline(track_spread_km=140.0, lead_hours=48)
    assert p_raw_high > p_raw_low

    p_log = cyclone_specialist.evaluate_spread_logistic_baseline(track_spread_km=85.0, lead_hours=48)
    assert 0.01 < p_log < 0.99


def test_cyclone_conformal_uncertainty(cyclone_specialist):
    """Test Level 5: Conformal track uncertainty radius."""
    r90 = cyclone_specialist.evaluate_conformal_track_radius(track_spread_km=85.0, lead_hours=48, target_coverage=0.90)
    r80 = cyclone_specialist.evaluate_conformal_track_radius(track_spread_km=85.0, lead_hours=48, target_coverage=0.80)
    assert r90 > r80 > 85.0


def test_cyclone_landfall_vs_non_landfall_null_safety(cyclone_specialist, nominal_cyclone_landfall_features):
    """Verify strict null-safety: landfall fields are present for landfall and None for offshore."""
    # Landfall case
    out_lf = cyclone_specialist.predict(nominal_cyclone_landfall_features)
    assert out_lf.landfall_location_failure_probability is not None
    assert out_lf.landfall_timing_failure_probability is not None

    # Non-landfall offshore case
    offshore_features = nominal_cyclone_landfall_features.model_copy(
        update={"forecast_landfall": False, "distance_to_coast_km": 500.0}
    )
    out_offshore = cyclone_specialist.predict(offshore_features)
    assert out_offshore.landfall_location_failure_probability is None
    assert out_offshore.landfall_timing_failure_probability is None
    # Track and intensity are still computed
    assert out_offshore.track_failure_probability is not None
    assert out_offshore.intensity_failure_probability is not None


def test_cyclone_ood_and_abstention(cyclone_specialist, nominal_cyclone_landfall_features):
    """Verify OOD detection and abstention state under extreme shear/spread."""
    ood_features = nominal_cyclone_landfall_features.model_copy(
        update={
            "ensemble_track_spread_km": 350.0,  # Exceeds 280km
            "vertical_wind_shear_ms": 52.0,     # Exceeds 45 m/s
        }
    )
    out = cyclone_specialist.predict(ood_features)
    assert out.ood is True

    state = cyclone_specialist.to_reliability_state(ood_features)
    assert state.abstention_state is True
    assert state.decision_mode == DecisionMode.ABSTAIN_UNSUPPORTED
    assert state.reliability_state == OperationalReliabilityState.ABSTAIN
    assert state.bust_probability is None


def test_cyclone_to_reliability_state_integration(cyclone_specialist, nominal_cyclone_landfall_features):
    """Verify universal ReliabilityState generation for cyclone."""
    state = cyclone_specialist.to_reliability_state(
        nominal_cyclone_landfall_features,
        forecast_id="FCST-TEST-FANI",
        location="ODISHA_COAST",
    )
    assert isinstance(state, ReliabilityState)
    assert state.forecast_identity == "FCST-TEST-FANI"
    assert state.hazard_type == "CYCLONE"
    assert state.bust_probability is not None
    assert len(state.hazard_curve) > 0
    assert len(state.survival_curve) == len(state.hazard_curve)

    # Invariant: Monotonic survival curve
    for i in range(len(state.survival_curve) - 1):
        assert state.survival_curve[i+1] <= state.survival_curve[i]

    assert state.decision_mode == DecisionMode.NOMINAL
    assert state.reliability_state == OperationalReliabilityState.STABLE


# ==============================================================================
# Monsoon and LPS Reliability Specialist Tests (Gate 5 / Phase F)
# ==============================================================================

@pytest.fixture
def monsoon_specialist():
    return MonsoonReliabilitySpecialist()


@pytest.fixture
def nominal_monsoon_features():
    return MonsoonIssueFeatures(
        lead_hours=48,
        system_type=MonsoonSystemType.MONSOON_DEPRESSION,
        regime_state=MonsoonRegimeState.ACTIVE_MONSOON,
        forecast_lat=21.2,
        forecast_lon=85.8,
        central_pressure_hpa=992.0,
        pressure_tendency_hpa_24h=-5.0,
        forward_speed_kmh=16.0,
        ensemble_track_spread_km=90.0,
        vorticity_850hpa_s=1.4e-4,
        vertical_wind_shear_ms=14.0,
        moisture_flux_transport_kg_ms=580.0,
        forecast_rainfall_max_24h_mm=135.0,
        ensemble_rainfall_spread_mm=38.0,
        monsoon_trough_displacement_km=-35.0,
        offshore_trough_present=True,
    )


def test_monsoon_baselines(monsoon_specialist):
    """Test Level 1, 2, 3 monsoon baselines."""
    p_clim = monsoon_specialist.evaluate_climatology_baseline(
        regime_state=MonsoonRegimeState.ACTIVE_MONSOON, lead_hours=48
    )
    assert 0.05 < p_clim < 0.50

    p_raw_low = monsoon_specialist.evaluate_raw_ensemble_baseline(track_spread_km=60.0, lead_hours=48)
    p_raw_high = monsoon_specialist.evaluate_raw_ensemble_baseline(track_spread_km=220.0, lead_hours=48)
    assert p_raw_high > p_raw_low

    p_log = monsoon_specialist.evaluate_spread_logistic_baseline(track_spread_km=90.0, lead_hours=48)
    assert 0.01 < p_log < 0.99


def test_monsoon_three_pillar_decomposition(monsoon_specialist, nominal_monsoon_features):
    """Verify separate evaluation of system dynamics, precipitation, and regime transitions."""
    out = monsoon_specialist.predict(nominal_monsoon_features)
    assert out.hazard == "MONSOON_LPS"

    # Pillar 1: System Dynamics
    assert out.system_location_failure_probability is not None
    assert out.propagation_speed_failure_probability is not None
    assert out.deepening_failure_probability is not None

    # Pillar 2: Precipitation
    assert out.rainfall_placement_failure_probability is not None
    assert out.rainfall_intensity_failure_probability is not None

    # Pillar 3: Regime Transition
    assert out.regime_transition_failure_probability is not None

    # Overall and evidence
    assert out.overall_reliability is not None
    assert len(out.evidence) >= 4
    assert out.ood is False


def test_monsoon_regime_states(monsoon_specialist, nominal_monsoon_features):
    """Verify regime sensitivity: transition states have higher regime transition risk."""
    out_active = monsoon_specialist.predict(nominal_monsoon_features)

    trans_features = nominal_monsoon_features.model_copy(
        update={"regime_state": MonsoonRegimeState.TRANSITION_TO_BREAK}
    )
    out_trans = monsoon_specialist.predict(trans_features)

    assert out_trans.regime_transition_failure_probability > out_active.regime_transition_failure_probability


def test_monsoon_ood_and_abstention(monsoon_specialist, nominal_monsoon_features):
    """Verify OOD detection and abstention under extreme moisture transport and track spread."""
    ood_features = nominal_monsoon_features.model_copy(
        update={
            "ensemble_track_spread_km": 380.0,            # Exceeds 300 km
            "vertical_wind_shear_ms": 55.0,               # Exceeds 50 m/s
            "moisture_flux_transport_kg_ms": 1800.0,      # Exceeds 1600 kg/(m*s)
        }
    )
    out = monsoon_specialist.predict(ood_features)
    assert out.ood is True

    state = monsoon_specialist.to_reliability_state(ood_features)
    assert state.abstention_state is True
    assert state.decision_mode == DecisionMode.ABSTAIN_UNSUPPORTED
    assert state.reliability_state == OperationalReliabilityState.ABSTAIN
    assert state.bust_probability is None


def test_monsoon_to_reliability_state_integration(monsoon_specialist, nominal_monsoon_features):
    """Verify universal ReliabilityState generation for Monsoon and LPS."""
    state = monsoon_specialist.to_reliability_state(
        nominal_monsoon_features,
        forecast_id="FCST-TEST-MONSOON-BOB",
        location="CENTRAL_INDIA_TROUGH",
    )
    assert isinstance(state, ReliabilityState)
    assert state.forecast_identity == "FCST-TEST-MONSOON-BOB"
    assert state.hazard_type == "MONSOON_LPS"
    assert state.bust_probability is not None
    assert len(state.hazard_curve) > 0
    assert len(state.survival_curve) == len(state.hazard_curve)

    # Invariant: Monotonic survival curve
    for i in range(len(state.survival_curve) - 1):
        assert state.survival_curve[i+1] <= state.survival_curve[i]

    assert state.decision_mode == DecisionMode.NOMINAL
    assert state.reliability_state == OperationalReliabilityState.STABLE


# ==============================================================================
# WESTERN DISTURBANCE RELIABILITY SPECIALIST TESTS (GATE 6 / P1)
# ==============================================================================

@pytest.fixture
def wd_specialist():
    return WesternDisturbanceReliabilitySpecialist()


@pytest.fixture
def nominal_wd_features():
    return WDIssueFeatures(
        lead_hours=48,
        intensity_class=WDIntensityClass.SEVERE_ACTIVE,
        terrain_regime=WDTerrainRegime.HIMALAYAN_HIGH_ALTITUDE,
        forecast_lat=34.1,
        forecast_lon=74.8,
        subtropical_jet_speed_ms=75.0,
        jet_core_lat_displacement_deg=-1.5,
        trough_depth_500hpa_gpm=5480.0,
        trough_tilt=WDTroughTilt.NEGATIVE,
        induced_low_present=True,
        ensemble_trough_spread_km=65.0,
        forecast_precip_max_24h_mm=85.0,
        ensemble_precip_spread_mm=22.0,
        forecast_duration_hours=48.0,
        freezing_level_m=2400.0,
        surface_temp_celsius=1.2,
        has_high_altitude_obs=True,
    )


def test_wd_baselines(wd_specialist):
    """Test Level 1, 2, 3 Western Disturbance baselines."""
    p_clim = wd_specialist.evaluate_climatology_baseline(
        terrain_regime=WDTerrainRegime.HIMALAYAN_HIGH_ALTITUDE, lead_hours=48
    )
    assert 0.05 < p_clim < 0.50

    p_raw_low = wd_specialist.evaluate_raw_ensemble_baseline(trough_spread_km=50.0, lead_hours=48)
    p_raw_high = wd_specialist.evaluate_raw_ensemble_baseline(trough_spread_km=210.0, lead_hours=48)
    assert p_raw_high > p_raw_low

    p_log = wd_specialist.evaluate_spread_logistic_baseline(trough_spread_km=80.0, lead_hours=48)
    assert 0.01 < p_log < 0.99


def test_wd_decomposed_failure_modes(wd_specialist, nominal_wd_features):
    """Verify separate evaluation of arrival, location, precip, displacement, duration, and rain/snow."""
    out = wd_specialist.predict(nominal_wd_features)
    assert out.hazard == "WESTERN_DISTURBANCE"

    assert out.arrival_failure_probability is not None
    assert out.track_location_failure_probability is not None
    assert out.precipitation_amount_failure_probability is not None
    assert out.precipitation_displacement_failure_probability is not None
    assert out.duration_failure_probability is not None
    assert out.rain_snow_partition_failure_probability is not None

    assert out.overall_reliability is not None
    assert len(out.evidence) >= 5
    assert out.ood is False


def test_wd_rain_snow_null_safety(wd_specialist, nominal_wd_features):
    """Verify rain/snow partition is strictly null when observations are unsupported."""
    no_obs_features = nominal_wd_features.model_copy(
        update={
            "has_high_altitude_obs": False,
            "freezing_level_m": None,
            "surface_temp_celsius": None,
        }
    )
    out = wd_specialist.predict(no_obs_features)
    assert out.rain_snow_partition_failure_probability is None

    # Evidence confirms null safety
    assert any("Rain/snow partition: null" in e for e in out.evidence)


def test_wd_terrain_conditioning(wd_specialist, nominal_wd_features):
    """Verify terrain conditioning: Himalayan high altitude has higher orographic precip bust risk."""
    out_himalayan = wd_specialist.predict(nominal_wd_features)

    plains_features = nominal_wd_features.model_copy(
        update={"terrain_regime": WDTerrainRegime.INDO_GANGETIC_PLAINS}
    )
    out_plains = wd_specialist.predict(plains_features)

    assert out_himalayan.precipitation_amount_failure_probability > out_plains.precipitation_amount_failure_probability


def test_wd_ood_and_abstention(wd_specialist, nominal_wd_features):
    """Verify OOD detection and abstention under extreme jet speed and trough spread."""
    ood_features = nominal_wd_features.model_copy(
        update={
            "ensemble_trough_spread_km": 320.0,       # Exceeds 280 km
            "subtropical_jet_speed_ms": 105.0,        # Exceeds 95 m/s
            "trough_depth_500hpa_gpm": 5150.0,        # Polar intrusion < 5250 gpm
        }
    )
    out = wd_specialist.predict(ood_features)
    assert out.ood is True

    state = wd_specialist.to_reliability_state(ood_features)
    assert state.abstention_state is True
    assert state.decision_mode == DecisionMode.ABSTAIN_UNSUPPORTED
    assert state.reliability_state == OperationalReliabilityState.ABSTAIN
    assert state.bust_probability is None


def test_wd_to_reliability_state_integration(wd_specialist, nominal_wd_features):
    """Verify universal ReliabilityState generation for Western Disturbance."""
    state = wd_specialist.to_reliability_state(
        nominal_wd_features,
        forecast_id="FCST-TEST-WD-HIMALAYA",
        location="WESTERN_HIMALAYAS_SRINAGAR",
    )
    assert isinstance(state, ReliabilityState)
    assert state.forecast_identity == "FCST-TEST-WD-HIMALAYA"
    assert state.hazard_type == "WESTERN_DISTURBANCE"
    assert state.bust_probability is not None
    assert len(state.hazard_curve) > 0
    assert len(state.survival_curve) == len(state.hazard_curve)

    # Invariant: Monotonic survival curve
    for i in range(len(state.survival_curve) - 1):
        assert state.survival_curve[i+1] <= state.survival_curve[i]

    assert state.decision_mode == DecisionMode.NOMINAL
    assert state.reliability_state == OperationalReliabilityState.STABLE


# ==============================================================================
# HEATWAVE AND SEVERE-WIND RELIABILITY SPECIALIST TESTS (GATE 7 / P1 + P2)
# ==============================================================================

@pytest.fixture
def hw_specialist():
    return HeatwaveReliabilitySpecialist()


@pytest.fixture
def nominal_hw_features():
    return HeatwaveIssueFeatures(
        lead_hours=48,
        regime=HeatwaveRegime.CORE_HEATWAVE_ZONE,
        severity=HeatwaveSeverity.SEVERE_HEATWAVE,
        forecast_lat=25.5,
        forecast_lon=82.0,
        forecast_tmax_celsius=45.5,
        forecast_tmin_celsius=31.5,
        climatological_normal_tmax_celsius=39.0,
        departure_tmax_celsius=6.5,
        ensemble_tmax_spread_celsius=2.8,
        ensemble_tmin_spread_celsius=1.6,
        soil_moisture_fraction=0.08,
        temp_advection_850hpa_k_s=2.5e-5,
        forecast_duration_days=6.0,
        wind_gust_10m_ms=18.5,
        ensemble_gust_spread_ms=3.2,
        has_paired_wind_data=True,
    )


def test_heatwave_baselines(hw_specialist):
    """Test Level 1, 2, 3 Heatwave baselines."""
    p_clim = hw_specialist.evaluate_climatology_baseline(
        regime=HeatwaveRegime.CORE_HEATWAVE_ZONE, lead_hours=48
    )
    assert 0.05 < p_clim < 0.50

    p_raw_low = hw_specialist.evaluate_raw_ensemble_baseline(tmax_spread_celsius=1.2, lead_hours=48)
    p_raw_high = hw_specialist.evaluate_raw_ensemble_baseline(tmax_spread_celsius=4.5, lead_hours=48)
    assert p_raw_high > p_raw_low

    p_log = hw_specialist.evaluate_spread_logistic_baseline(tmax_spread_celsius=2.5, lead_hours=48)
    assert 0.01 < p_log < 0.99


def test_heatwave_decomposed_failure_modes(hw_specialist, nominal_hw_features):
    """Verify separate evaluation of threshold, peak, onset, duration, warm night, spatial, and wind."""
    out = hw_specialist.predict(nominal_hw_features)
    assert out.hazard == "HEATWAVE"

    assert out.threshold_failure_probability is not None
    assert out.peak_temperature_failure_probability is not None
    assert out.onset_failure_probability is not None
    assert out.duration_failure_probability is not None
    assert out.warm_night_failure_probability is not None
    assert out.spatial_extent_failure_probability is not None
    assert out.severe_wind_failure_probability is not None

    assert out.overall_reliability is not None
    assert len(out.evidence) >= 5
    assert out.ood is False


def test_heatwave_severe_wind_null_safety(hw_specialist, nominal_hw_features):
    """Verify severe wind failure probability is strictly null when paired data is absent."""
    no_wind_features = nominal_hw_features.model_copy(
        update={
            "has_paired_wind_data": False,
            "wind_gust_10m_ms": None,
            "ensemble_gust_spread_ms": None,
        }
    )
    out = hw_specialist.predict(no_wind_features)
    assert out.severe_wind_failure_probability is None

    # Evidence confirms null safety
    assert any("Severe wind module: null" in e for e in out.evidence)


def test_heatwave_regional_conditioning(hw_specialist, nominal_hw_features):
    """Verify regional conditioning: Core zone with dry soil has higher peak temperature bust risk."""
    out_core = hw_specialist.predict(nominal_hw_features)

    coastal_features = nominal_hw_features.model_copy(
        update={"regime": HeatwaveRegime.COASTAL_PENINSULAR, "soil_moisture_fraction": 0.35}
    )
    out_coastal = hw_specialist.predict(coastal_features)

    assert out_core.peak_temperature_failure_probability > out_coastal.peak_temperature_failure_probability


def test_heatwave_ood_and_abstention(hw_specialist, nominal_hw_features):
    """Verify OOD detection and abstention under extreme thermal anomaly and spread."""
    ood_features = nominal_hw_features.model_copy(
        update={
            "ensemble_tmax_spread_celsius": 8.5,       # Exceeds 6.0°C
            "departure_tmax_celsius": 14.0,            # Exceeds 12.0°C
            "soil_moisture_fraction": 0.005,           # Extreme depletion < 0.02
        }
    )
    out = hw_specialist.predict(ood_features)
    assert out.ood is True

    state = hw_specialist.to_reliability_state(ood_features)
    assert state.abstention_state is True
    assert state.decision_mode == DecisionMode.ABSTAIN_UNSUPPORTED
    assert state.reliability_state == OperationalReliabilityState.ABSTAIN
    assert state.bust_probability is None


def test_heatwave_to_reliability_state_integration(hw_specialist, nominal_hw_features):
    """Verify universal ReliabilityState generation for Heatwave."""
    state = hw_specialist.to_reliability_state(
        nominal_hw_features,
        forecast_id="FCST-TEST-HW-COREZONE",
        location="NORTH_CENTRAL_PLAINS",
    )
    assert isinstance(state, ReliabilityState)
    assert state.forecast_identity == "FCST-TEST-HW-COREZONE"
    assert state.hazard_type == "HEATWAVE"
    assert state.bust_probability is not None
    assert len(state.hazard_curve) > 0
    assert len(state.survival_curve) == len(state.hazard_curve)

    # Invariant: Monotonic survival curve
    for i in range(len(state.survival_curve) - 1):
        assert state.survival_curve[i+1] <= state.survival_curve[i]

    assert state.decision_mode == DecisionMode.NOMINAL
    assert state.reliability_state == OperationalReliabilityState.STABLE

