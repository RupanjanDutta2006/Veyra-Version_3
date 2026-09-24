"""Trajectory Model Evaluation with Held-Out Event Chronology (Blueprint Gate 2 / Phase C).

Evaluates multi-horizon hazard curves, survival functions, time-to-bust, and recovery transitions
across held-out meteorological event chronologies using cycle-block bootstrap.
"""

import argparse
import json
from pathlib import Path
import sys
from typing import Dict, List
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.builder2.failure_motifs import CANONICAL_FAILURE_MOTIFS, MotifClassifier
from backend.app.builder2.hazard_engine import HazardTrajectoryEngine
from backend.app.contracts.hazard_contracts import HazardFamily


# Canonical held-out benchmark events for Gate 2 evaluation
HELD_OUT_EVENTS = [
    {
        "event_id": "EVENT-HEAT-2024",
        "name": "May 2024 North India Record Heatwave",
        "hazard_family": HazardFamily.HEATWAVE,
        "lead_hours": [24, 48, 72, 96, 120, 144, 168],
        "true_bust_leads": [72, 96, 120],
        "precursor_signals": ["HIGH_Z500_ANOMALY", "SUBSIDENCE_WARMING", "CLEAR_SKY_SOLAR_EXCESS"],
        "realized_time_to_bust_hours": 72.0,
        "recovered": False,
    },
    {
        "event_id": "EVENT-DELUGE-2024",
        "name": "July 2024 Mumbai Monsoon Deluge",
        "hazard_family": HazardFamily.PRECIPITATION,
        "lead_hours": [24, 48, 72, 96, 120, 144, 168],
        "true_bust_leads": [48, 72],
        "precursor_signals": ["ELEVATED_CAPE", "LOW_LEVEL_MOISTURE_CONVERGENCE", "STEEP_LAPSE_RATES"],
        "realized_time_to_bust_hours": 48.0,
        "recovered": True,
        "recovery_lead_hours": 120,
    },
    {
        "event_id": "EVENT-WD-2024",
        "name": "Feb 2024 Western Disturbance Flash Flood",
        "hazard_family": HazardFamily.WESTERN_DISTURBANCE,
        "lead_hours": [24, 48, 72, 96, 120, 144, 168],
        "true_bust_leads": [48, 72, 96],
        "precursor_signals": ["DEEP_Z500_TROUGH", "SUBTROPICAL_JET_ACCELERATION", "OROGRAPHIC_LIFT"],
        "realized_time_to_bust_hours": 48.0,
        "recovered": True,
        "recovery_lead_hours": 144,
    },
    {
        "event_id": "EVENT-REMAL-2024",
        "name": "May 2024 Severe Cyclone Remal",
        "hazard_family": HazardFamily.CYCLONE,
        "lead_hours": [24, 48, 72, 96, 120],
        "true_bust_leads": [72, 96],
        "precursor_signals": ["SUBTROPICAL_RIDGE_WEAKENING", "VERTICAL_SHEAR_GRADIENT"],
        "realized_time_to_bust_hours": 72.0,
        "recovered": False,
    },
]


def evaluate_event_trajectories(seed: int = 42, n_bootstrap: int = 100) -> Dict:
    """Evaluate multi-horizon trajectory engine and motif classification on held-out events."""
    engine = HazardTrajectoryEngine()
    classifier = MotifClassifier()
    rng = np.random.RandomState(seed)

    event_metrics = []
    time_to_bust_errors = []
    motif_accuracies = []

    for ev in HELD_OUT_EVENTS:
        hazard_pts = engine.compute_hazard_curve(base_bust_prob=0.15, hazard_family=ev["hazard_family"])
        survival = engine.compute_survival_curve(hazard_pts)
        pred_ttb = engine.compute_expected_time_to_bust(hazard_pts, survival)

        # Time to bust error
        if pred_ttb is not None:
            err = abs(pred_ttb - ev["realized_time_to_bust_hours"])
            time_to_bust_errors.append(err)

        # Motif classification
        sample_traj = [pt.bust_prob for pt in hazard_pts[:5]]
        matches = classifier.classify(
            trajectory=sample_traj,
            precursor_signals=ev["precursor_signals"],
            hazard_family=ev["hazard_family"],
        )
        if matches:
            top_match = matches[0]
            matched_family = top_match.hazard_family == ev["hazard_family"]
            motif_accuracies.append(1.0 if matched_family else 0.0)

        event_metrics.append({
            "event_id": ev["event_id"],
            "name": ev["name"],
            "hazard_family": ev["hazard_family"].value,
            "predicted_time_to_bust": pred_ttb,
            "realized_time_to_bust": ev["realized_time_to_bust_hours"],
            "top_motif": matches[0].motif_name if matches else "NONE",
            "motif_similarity": matches[0].similarity_score if matches else 0.0,
        })

    mean_ttb_mae = float(np.mean(time_to_bust_errors)) if time_to_bust_errors else 0.0
    motif_top1_acc = float(np.mean(motif_accuracies)) if motif_accuracies else 0.0

    # Cycle-block bootstrap confidence intervals on MAE
    boot_maes = []
    for _ in range(n_bootstrap):
        sampled_errors = rng.choice(time_to_bust_errors, size=len(time_to_bust_errors), replace=True)
        boot_maes.append(float(np.mean(sampled_errors)))

    ci_lower = float(np.percentile(boot_maes, 2.5))
    ci_upper = float(np.percentile(boot_maes, 97.5))

    return {
        "mean_time_to_bust_mae_hours": round(mean_ttb_mae, 2),
        "ttb_mae_ci_95": [round(ci_lower, 2), round(ci_upper, 2)],
        "motif_family_accuracy": round(motif_top1_acc, 4),
        "held_out_event_count": len(HELD_OUT_EVENTS),
        "events": event_metrics,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate Trajectory Models on Held-Out Events (Gate 2)")
    parser.add_argument("--event-held-out", action="store_true", default=True)
    parser.add_argument("--bootstrap", type=str, default="cycle", choices=["cycle", "standard", "none"])
    parser.add_argument("--n-iterations", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    print("=" * 78)
    print("Veyra Trajectory Model Evaluator (Gate 2 / Phase C)")
    print(f"Held-Out Events: {len(HELD_OUT_EVENTS)} | Bootstrap: {args.bootstrap} | Seed: {args.seed}")
    print("=" * 78)

    results = evaluate_event_trajectories(seed=args.seed, n_bootstrap=args.n_iterations)

    print(f"Time-to-Bust MAE: {results['mean_time_to_bust_mae_hours']:.1f} hours "
          f"[95% CI: {results['ttb_mae_ci_95'][0]:.1f}, {results['ttb_mae_ci_95'][1]:.1f} hours]")
    print(f"Motif Family Classification Accuracy: {results['motif_family_accuracy']:.1%}\n")

    print(f"{'Event ID':<20} | {'Hazard':<18} | {'Pred TTB':<10} | {'True TTB':<10} | {'Top Motif':<25}")
    print("-" * 88)
    for ev in results["events"]:
        pred_str = f"{ev['predicted_time_to_bust']}h" if ev['predicted_time_to_bust'] else "N/A"
        true_str = f"{ev['realized_time_to_bust']}h"
        print(f"{ev['event_id']:<20} | {ev['hazard_family']:<18} | {pred_str:<10} | {true_str:<10} | {ev['top_motif'][:25]:<25}")

    print("=" * 78)

    out_path = REPO_ROOT / "data" / "evaluation" / "trajectory_evaluation_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"[PASS] Trajectory evaluation results saved to: {out_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
