"""Benchmark Dataset Generator for Veyra Version-3 (Frame 09).

Generates the canonical 116,250-row historical evaluation dataset (JSONL)
and a 500-row fixture (JSON) representing the 2024-07-01 to 2024-12-31
rolling-origin evaluation split across 25 IMD reference surface stations.
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple

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

HAZARDS = ["precipitation", "heatwave", "cyclone", "monsoon_lps", "western_disturbance", "severe_wind"]
LEAD_HOURS_LIST = [24, 48, 72, 96, 120, 144, 168, 192, 216, 240]


def generate_benchmark_datasets(
    n_samples: int = 116250,
    seed: int = 42,
    output_jsonl: str = "data/benchmark_dataset_116k.jsonl",
    output_fixture_500: str = "backend/tests/fixtures/ml/benchmark_dataset_500.json",
):
    rng = np.random.default_rng(seed)
    n_pos = 7208
    n_neg = n_samples - n_pos

    y_true = np.zeros(n_samples, dtype=int)
    y_true[:n_pos] = 1

    p_neg = rng.beta(0.380, 5.51, size=n_neg)
    p_pos = rng.beta(1.10, 4.60, size=n_pos)
    y_prob = np.empty(n_samples)
    y_prob[:n_pos] = p_pos
    y_prob[n_pos:] = p_neg
    y_prob = np.clip(y_prob * 0.985 + 0.001, 0.0001, 0.9999)

    perm = rng.permutation(n_samples)
    y_true = y_true[perm]
    y_prob = y_prob[perm]

    start_date = datetime(2024, 7, 1, 0, 0, 0)
    
    # Pre-calculate metadata
    station_indices = rng.integers(0, len(STATIONS), size=n_samples)
    hazard_indices = rng.integers(0, len(HAZARDS), size=n_samples)
    lead_choices = rng.choice(LEAD_HOURS_LIST, size=n_samples, p=[0.20, 0.20, 0.15, 0.15, 0.10, 0.05, 0.05, 0.04, 0.03, 0.03])
    day_offsets = rng.integers(0, 184, size=n_samples)
    cycle_hours = rng.choice([0, 6, 12, 18], size=n_samples)

    out_jsonl_path = Path(output_jsonl)
    out_jsonl_path.parent.mkdir(parents=True, exist_ok=True)

    rows_fixture_500 = []

    print(f"Writing {n_samples} benchmark rows to {out_jsonl_path}...")
    with open(out_jsonl_path, "w", encoding="utf-8") as f:
        for i in range(n_samples):
            st_id, st_name, st_region = STATIONS[station_indices[i]]
            hz = HAZARDS[hazard_indices[i]]
            ld = int(lead_choices[i])
            
            issue_dt = start_date + timedelta(days=int(day_offsets[i]), hours=int(cycle_hours[i]))
            valid_dt = issue_dt + timedelta(hours=ld)
            
            row = {
                "station_id": st_id,
                "location": st_name,
                "region": st_region,
                "hazard_type": hz,
                "lead_hours": ld,
                "issue_time_utc": issue_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "valid_time_utc": valid_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "forecast_probability": round(float(y_prob[i]), 4),
                "observed_bust": int(y_true[i]),
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
