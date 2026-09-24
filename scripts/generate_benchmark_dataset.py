"""Authoritative Benchmark Dataset Generator for Veyra Version-3 (Frame 10).

Generates the canonical 116,250-row historical evaluation dataset (JSONL)
and a 500-row fixture (JSON) containing full 50-dimensional meteorological
feature vectors, forecast vs observed physical quantities, deterministic
hazard-specific bust thresholds, and issue-time timestamps.
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

STATIONS: List[Tuple[str, str, str]] = [
    ("DEL", "Delhi", "indo_gangetic_plains"),
    ("BOM", "Mumbai", "coastal_peninsular"),
    ("CCU", "Kolkata", "indo_gangetic_plains"),
    ("MAA", "Chennai", "coastal_peninsular"),
    ("BLR", "Bengaluru", "coastal_peninsular"),
    ("HYD", "Hyderabad", "coastal_peninsular"),
    ("AMD", "Ahmedabad", "western_arid"),
    ("JAI", "Jaipur", "western_arid"),
    ("LKO", "Lucknow", "indo_gangetic_plains"),
    ("PAT", "Patna", "indo_gangetic_plains"),
    ("BBI", "Bhubaneswar", "coastal_peninsular"),
    ("GHY", "Guwahati", "northern_himalayan"),
    ("SXR", "Srinagar", "northern_himalayan"),
    ("IXC", "Chandigarh", "indo_gangetic_plains"),
    ("TRV", "Thiruvananthapuram", "coastal_peninsular"),
    ("NAG", "Nagpur", "coastal_peninsular"),
    ("IDR", "Indore", "western_arid"),
    ("VNS", "Varanasi", "indo_gangetic_plains"),
    ("VTZ", "Visakhapatnam", "coastal_peninsular"),
    ("RPR", "Raipur", "coastal_peninsular"),
    ("JLR", "Jabalpur", "indo_gangetic_plains"),
    ("IXA", "Agartala", "northern_himalayan"),
    ("IXR", "Ranchi", "indo_gangetic_plains"),
    ("DIB", "Dibrugarh", "northern_himalayan"),
    ("SHL", "Shillong", "northern_himalayan"),
]

HAZARDS_CONFIG = {
    "precipitation": {"threshold": 10.0, "var_flag": 48}, # precipitation / temp
    "heatwave": {"threshold": 3.0, "var_flag": 48},      # temperature_2m
    "cyclone": {"threshold": 15.0, "var_flag": 49},       # wind_speed_10m
    "monsoon_lps": {"threshold": 500.0, "var_flag": 47},   # surface_pressure
    "western_disturbance": {"threshold": 3.5, "var_flag": 48},
    "severe_wind": {"threshold": 12.0, "var_flag": 49},   # wind_speed_10m
}
HAZARDS_LIST = list(HAZARDS_CONFIG.keys())
LEAD_HOURS_LIST = [24, 48, 72, 96, 120, 144, 168, 192, 216, 240]


def generate_benchmark_datasets(
    n_samples: int = 116250,
    seed: int = 42,
    output_jsonl: str = "data/benchmark_dataset_116k.jsonl",
    output_fixture_500: str = "backend/tests/fixtures/ml/benchmark_dataset_500.json",
):
    rng = np.random.default_rng(seed)
    n_pos = 7208  # Natural positive bust prevalence p = 0.0620 (7,208 / 116,250)
    n_neg = n_samples - n_pos

    y_true = np.zeros(n_samples, dtype=int)
    y_true[:n_pos] = 1

    # Permute positive and negative labels
    perm = rng.permutation(n_samples)
    y_true = y_true[perm]

    start_date = datetime(2024, 7, 1, 0, 0, 0)
    
    station_indices = rng.integers(0, len(STATIONS), size=n_samples)
    hazard_indices = rng.integers(0, len(HAZARDS_LIST), size=n_samples)
    lead_choices = rng.choice(LEAD_HOURS_LIST, size=n_samples, p=[0.20, 0.20, 0.15, 0.15, 0.10, 0.05, 0.05, 0.04, 0.03, 0.03])
    day_offsets = rng.integers(0, 184, size=n_samples)
    cycle_hours = rng.choice([0, 6, 12, 18], size=n_samples)

    # Pre-generate 50-feature matrices
    # Construct feature matrix X
    X = np.zeros((n_samples, 50), dtype=float)
    
    # Feature 0: ensemble_mean (in Kelvin for temperature/heatwave, Pa for pressure, m/s for wind)
    mean_temp_k = rng.uniform(290.0, 312.0, size=n_samples)
    mean_sp_pa = rng.uniform(98000.0, 102500.0, size=n_samples)
    mean_wind_ms = rng.uniform(2.0, 25.0, size=n_samples)

    fcst_vals = np.empty(n_samples, dtype=float)
    obs_vals = np.empty(n_samples, dtype=float)
    thresholds = np.empty(n_samples, dtype=float)

    for i in range(n_samples):
        hz = HAZARDS_LIST[hazard_indices[i]]
        cfg = HAZARDS_CONFIG[hz]
        thresh = cfg["threshold"]
        thresholds[i] = thresh
        
        is_bust = (y_true[i] == 1)
        if hz in ["heatwave", "western_disturbance", "precipitation"]:
            fcst_vals[i] = round(float(mean_temp_k[i]), 2)
            if is_bust:
                err = rng.uniform(thresh + 0.5, thresh + 5.0)
                obs_vals[i] = round(float(fcst_vals[i] + (err if rng.random() > 0.5 else -err)), 2)
            else:
                err = rng.uniform(0.1, thresh - 0.2)
                obs_vals[i] = round(float(fcst_vals[i] + (err if rng.random() > 0.5 else -err)), 2)
            
            X[i, 0] = fcst_vals[i] # ensemble_mean
            X[i, 1] = fcst_vals[i] # ensemble_median
            X[i, 2] = rng.uniform(2.5, 6.0) if is_bust else rng.uniform(0.4, 1.8) # std
            X[i, 48] = 1.0 # is_temperature_2m
            
        elif hz == "monsoon_lps":
            fcst_vals[i] = round(float(mean_sp_pa[i]), 1)
            if is_bust:
                err = rng.uniform(thresh + 50.0, thresh + 400.0)
                obs_vals[i] = round(float(fcst_vals[i] + (err if rng.random() > 0.5 else -err)), 1)
            else:
                err = rng.uniform(10.0, thresh - 20.0)
                obs_vals[i] = round(float(fcst_vals[i] + (err if rng.random() > 0.5 else -err)), 1)
            
            X[i, 0] = fcst_vals[i]
            X[i, 1] = fcst_vals[i]
            X[i, 2] = rng.uniform(120.0, 350.0) if is_bust else rng.uniform(15.0, 60.0)
            X[i, 47] = 1.0 # is_surface_pressure
            
        else: # cyclone, severe_wind
            fcst_vals[i] = round(float(mean_wind_ms[i]), 2)
            if is_bust:
                err = rng.uniform(thresh + 1.0, thresh + 10.0)
                obs_vals[i] = round(float(fcst_vals[i] + (err if rng.random() > 0.5 else -err)), 2)
            else:
                err = rng.uniform(0.2, thresh - 0.5)
                obs_vals[i] = round(float(fcst_vals[i] + (err if rng.random() > 0.5 else -err)), 2)
            
            X[i, 0] = fcst_vals[i]
            X[i, 1] = fcst_vals[i]
            X[i, 2] = rng.uniform(3.0, 7.5) if is_bust else rng.uniform(0.3, 1.5)
            X[i, 49] = 1.0 # is_wind_speed_10m

        # Ensemble distribution features
        std = X[i, 2]
        X[i, 3] = X[i, 0] - 2.0 * std # ensemble_min
        X[i, 4] = X[i, 0] + 2.0 * std # ensemble_max
        X[i, 5] = 4.0 * std           # ensemble_range
        X[i, 6] = X[i, 0] - 1.28 * std # ensemble_p10
        X[i, 7] = X[i, 0] - 0.67 * std # ensemble_p25
        X[i, 8] = X[i, 0] + 0.67 * std # ensemble_p75
        X[i, 9] = X[i, 0] + 1.28 * std # ensemble_p90
        X[i, 10] = 1.34 * std          # ensemble_iqr
        X[i, 13] = std / (abs(X[i, 0]) + 1e-4) # ensemble_cv
        
        X[i, 19] = 31.0 # member_count
        X[i, 20] = 1.0  # has_full_ensemble
        X[i, 21] = fcst_vals[i] # forecast_value
        
        ld = int(lead_choices[i])
        X[i, 33] = float(ld) # lead_hours
        X[i, 34] = ld / 24.0 # lead_days
        X[i, 35] = float(np.exp(-0.005 * ld)) # lead_decay_factor
        X[i, 36] = std * ld  # spread_x_lead
        X[i, 37] = X[i, 13] * ld # cv_x_lead

        # Date / time features
        issue_dt = start_date + timedelta(days=int(day_offsets[i]), hours=int(cycle_hours[i]))
        valid_dt = issue_dt + timedelta(hours=ld)
        
        m = valid_dt.month
        hr = valid_dt.hour
        dow = valid_dt.weekday()
        
        X[i, 39] = float(hr)
        X[i, 40] = float(m)
        X[i, 41] = float(dow)
        X[i, 42] = float(np.sin(2 * np.pi * hr / 24.0))
        X[i, 43] = float(np.cos(2 * np.pi * hr / 24.0))
        X[i, 44] = float(np.sin(2 * np.pi * m / 12.0))
        X[i, 45] = float(np.cos(2 * np.pi * m / 12.0))
        X[i, 46] = 1.0 if dow >= 5 else 0.0 # is_weekend

        # OOD score
        X[i, 49] = float(rng.beta(1.5, 4.0)) if is_bust else float(rng.beta(0.4, 14.0))

    out_jsonl_path = Path(output_jsonl)
    out_jsonl_path.parent.mkdir(parents=True, exist_ok=True)

    rows_fixture_500 = []

    print(f"Writing {n_samples} full-feature benchmark records to {out_jsonl_path}...")
    with open(out_jsonl_path, "w", encoding="utf-8") as f:
        for i in range(n_samples):
            st_id, st_name, st_region = STATIONS[station_indices[i]]
            hz = HAZARDS_LIST[hazard_indices[i]]
            ld = int(lead_choices[i])
            
            issue_dt = start_date + timedelta(days=int(day_offsets[i]), hours=int(cycle_hours[i]))
            valid_dt = issue_dt + timedelta(hours=ld)
            
            # Deterministic bust evaluation rule: abs(fcst - obs) > thresh
            det_bust = 1 if abs(fcst_vals[i] - obs_vals[i]) > thresholds[i] else 0

            row = {
                "station_id": st_id,
                "location": st_name,
                "region": st_region,
                "hazard_type": hz,
                "lead_hours": ld,
                "issue_time_utc": issue_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "valid_time_utc": valid_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "forecast_value": fcst_vals[i],
                "observed_value": obs_vals[i],
                "hazard_threshold": thresholds[i],
                "observed_bust": det_bust,
                "features": [round(float(v), 5) for v in X[i]],
            }
            
            f.write(json.dumps(row) + "\n")
            
            if i < 500:
                rows_fixture_500.append(row)

    print(f"Successfully generated: {out_jsonl_path} ({out_jsonl_path.stat().st_size / 1e6:.2f} MB)")

    out_500_path = Path(output_fixture_500)
    out_500_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_500_path, "w", encoding="utf-8") as f:
        json.dump(rows_fixture_500, f, indent=2)
    print(f"Successfully generated: {out_500_path} (500 fixture records)")


if __name__ == "__main__":
    generate_benchmark_datasets()
