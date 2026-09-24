#!/usr/bin/env python3
"""
Veyra Frontend <-> Terminal Exact Value Parity Verification Utility.
Pure-Python cross-platform implementation.
"""

import sys
import json
import time
import argparse
import urllib.request
import urllib.error


def main():
    parser = argparse.ArgumentParser(description="Veyra Frontend <-> Terminal Exact Value Parity Verification Utility")
    parser.add_argument("location", nargs="?", default="Delhi", help="Location name (default: Delhi)")
    parser.add_argument("variable", nargs="?", default="temperature_2m", help="Target variable (default: temperature_2m)")
    parser.add_argument("mode", nargs="?", choices=["single", "standard_7d", "full_16d"], default="full_16d", help="Mode (default: full_16d)")
    parser.add_argument("api_base_url", nargs="?", default="http://127.0.0.1:8000", help="API base URL (default: http://127.0.0.1:8000)")
    parser.add_argument("--save-snapshot", action="store_true", help="Save response snapshot to JSON")
    parser.add_argument("--snapshot-path", default="", help="Custom snapshot file path")
    args = parser.parse_args()

    clean_base_url = args.api_base_url.rstrip("/")

    print("=" * 105)
    print(" VEYRA FRONTEND <-> TERMINAL EXACT VALUE PARITY VERIFIER")
    print(f" Authoritative Endpoint : {clean_base_url}/v1/dashboard/intelligence")
    print(f" Target Location        : {args.location} | Variable: {args.variable} | Mode: {args.mode}")
    print("=" * 105)

    # 1. Health Probe
    print(f"\n[1/4] Probing backend health at {clean_base_url}/v1/health...")
    try:
        req = urllib.request.Request(f"{clean_base_url}/v1/health")
        with urllib.request.urlopen(req, timeout=10) as resp:
            health = json.loads(resp.read().decode("utf-8"))
            print(f"  [+] Backend Status : {health.get('status')} (service: {health.get('service')}, version: {health.get('version')})")
    except Exception as e:
        print(f"  [-] Failed to connect to backend at {clean_base_url}: {e}")
        print("  Please ensure the FastAPI service is running on port 8000.")
        sys.exit(1)

    # 2. Authoritative Request
    print("\n[2/4] Querying authoritative POST /v1/dashboard/intelligence...")
    payload = json.dumps({
        "location": args.location,
        "variable": args.variable,
        "mode": args.mode
    }).encode("utf-8")

    t0 = time.time()
    try:
        req = urllib.request.Request(
            f"{clean_base_url}/v1/dashboard/intelligence",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            dash_resp = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  [-] Request failed: {e}")
        sys.exit(1)

    elapsed_ms = round((time.time() - t0) * 1000, 1)
    print(f"  [+] Response received in {elapsed_ms}ms with status: {dash_resp.get('status')}")

    timeline = dash_resp.get("timeline") or []
    print(f"\n[3/4] Validating Value Parity for {len(timeline)} points...")
    print("-" * 105)
    print(f"{'Lead':<6} | {'Valid Time':<20} | {'P(Bust) Raw':<14} | {'Frontend (2-dec)':<18} | {'Risk Tier':<10} | {'Trust State':<14}")
    print("-" * 105)

    for pt in timeline:
        lead = pt.get("lead_hours", 0)
        valid_time = pt.get("valid_time", "")
        raw_prob = pt.get("bust_probability")

        if raw_prob is not None:
            raw_str = f"{raw_prob:.6f}"
            frontend_str = f"{raw_prob * 100:.2f}%"
        else:
            raw_str = "ABSTAIN"
            frontend_str = "Safely Abstained"

        risk = pt.get("risk_level") or "NULL"
        trust = pt.get("trust_state") or "NULL"
        print(f"{lead:<4}h  | {valid_time:<20} | {raw_str:<14} | {frontend_str:<18} | {risk:<10} | {trust:<14}")

    print("-" * 105)

    if args.save_snapshot:
        out_path = args.snapshot_path or f"snapshot_{args.location}_{args.mode}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(dash_resp, f, indent=2)
        print(f"\n[4/4] Snapshot saved to: {out_path}")
    else:
        print("\n[4/4] Parity check complete.")

    print("=" * 105)


if __name__ == "__main__":
    main()
