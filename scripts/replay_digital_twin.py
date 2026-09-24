"""Replay severe weather episode via Reliability Digital Twin (Gate G11 / Phase 5).

Demonstrates comparative reliability tracking across Raw Ensemble, V3 Challenger,
Certified Veyra, and Frontier AI models over severe atmospheric events.

Operating in explicit SYNTHETIC demonstration mode unless grounded in physical truth.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

# Ensure repository root is in sys.path dynamically
CURRENT_DIR = Path.cwd()
if (CURRENT_DIR / "backend").is_dir():
    REPO_ROOT = CURRENT_DIR
elif (CURRENT_DIR / "repos" / "repo_b" / "backend").is_dir():
    REPO_ROOT = CURRENT_DIR / "repos" / "repo_b"
else:
    REPO_ROOT = Path(__file__).resolve().parent.parent

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.builder2.digital_twin_engine import DigitalTwinEngine
try:
    from backend.app.core.replay_modes import ReplayMode, create_synthetic_replay_record
except ImportError:
    create_synthetic_replay_record = None


def main():
    parser = argparse.ArgumentParser(description="Replay severe weather episode via Reliability Digital Twin.")
    parser.add_argument(
        "--mode",
        type=str,
        default="synthetic",
        choices=["synthetic", "historical"],
        help="Replay execution mode (synthetic demonstration or historical replay).",
    )
    parser.add_argument(
        "--fixtures",
        type=str,
        default="artifacts/synthetic_twin_fixture",
        help="Path to fixture directory for digital twin replay.",
    )
    parser.add_argument(
        "--event",
        type=str,
        default="historical",
        help="Historical severe weather event key (e.g. historical, cyclone_biparjoy_2023).",
    )
    parser.add_argument(
        "--compare",
        type=str,
        default="raw,v3,certified-veyra,frontier",
        help="Comma-separated list of tiers to compare (raw,v3,certified-veyra,frontier).",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="Optional path to export machine-readable JSON replay contract report.",
    )
    args = parser.parse_args()

    if args.mode == "synthetic":
        print("[NOTICE] Digital Twin operating in explicit SYNTHETIC demonstration mode.")

    tiers = [t.strip() for t in args.compare.split(",") if t.strip()]

    print(f"=== Veyra Reliability Digital Twin Replay (Gate 11 / Phase 5) ===")
    print(f"Event: {args.event}")
    print(f"Compared Tiers: {tiers}\n")

    engine = DigitalTwinEngine()
    result = engine.replay_event(event_name=args.event, compare_tiers=tiers)

    print(f"Event Replayed: {result.event_name}")
    print(f"Hazard Family: {result.hazard_family}")
    print(f"Total Forecast Cycles: {len(result.cycles)}\n")

    print(f"{'Cycle ID':<10} | {'Lead (h)':<8} | {'Raw Prob':<10} | {'V3 Prob':<10} | {'Cert Veyra':<12} | {'Frontier':<10} | {'Obs Bust'}")
    print("-" * 85)
    for c in result.cycles:
        print(
            f"{c.cycle_id:<10} | {c.lead_hours:<8} | {c.raw_bust_prob:<10.2f} | {c.v3_bust_prob:<10.2f} | "
            f"{c.certified_veyra_bust_prob:<12.2f} | {c.frontier_bust_prob:<10.2f} | {c.ground_truth_failure}"
        )

    print("\n=== Multi-Tier Summary Metrics ===")
    print(f"{'Tier':<16} | {'Brier':<8} | {'ECE':<8} | {'Lead Adv (h)':<13} | {'False Alarm':<12} | {'Utility':<8} | {'Latency':<9} | {'Status'}")
    print("-" * 95)
    for t_name, summary in result.tier_summaries.items():
        sim_tag = " [SIM]" if summary.is_simulation else ""
        print(
            f"{summary.tier_name + sim_tag:<16} | {summary.brier_score:<8.4f} | {summary.expected_calibration_error:<8.4f} | "
            f"{summary.lead_time_advantage_hours:<13.1f} | {summary.false_alarm_rate:<12.2f} | {summary.operational_utility_score:<8.2f} | "
            f"{summary.average_latency_ms:<7.1f}ms | {summary.status}"
        )

    print(f"\nRecommended Tier: {result.recommended_tier}")
    print(f"Rationale: {result.decision_rationale}")

    # Build provenance record
    if create_synthetic_replay_record:
        contract = create_synthetic_replay_record(
            provenance="Reliability Digital Twin Scenario Generator (Simulated Atmospheric Stress)",
            scenario_id=f"TWIN-{args.event.upper()}",
            disclosure_notice="[NOTICE] Digital Twin operating in explicit SYNTHETIC demonstration mode.",
        )
        record = contract.to_dict()
    else:
        record = {
            "mode": "synthetic",
            "provenance": "Reliability Digital Twin Scenario Generator (Simulated Atmospheric Stress)",
            "is_synthetic": True,
            "is_independent_truth": False,
            "scenario_id": f"TWIN-{args.event.upper()}",
            "disclosure_notice": "[NOTICE] Digital Twin operating in explicit SYNTHETIC demonstration mode.",
        }

    record["recommended_tier"] = result.recommended_tier
    record["total_cycles"] = len(result.cycles)

    if args.output_json:
        out_path = Path(args.output_json)
        if not out_path.is_absolute():
            out_path = REPO_ROOT / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)
        print(f"Digital Twin replay contract exported to: {out_path}")

    print("\n[PASS] Digital Twin synthetic replay completed with explicit disclosures.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
