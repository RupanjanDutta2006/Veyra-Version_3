#!/usr/bin/env python3
"""
Authoritative 16-Day Forecast Bust Trajectory Verification Utility for Veyra.
Cross-platform pure-Python implementation.
"""

import sys
import json
import time
import argparse
import urllib.request
import urllib.error


def main():
    parser = argparse.ArgumentParser(description="Authoritative 16-Day Forecast Bust Trajectory Verification Utility for Veyra")
    parser.add_argument("location", nargs="?", default="Delhi", help="Location name, station, or coordinates (default: Delhi)")
    parser.add_argument("variable", nargs="?", default="temperature_2m", help="Target variable (default: temperature_2m)")
    parser.add_argument("base_url", nargs="?", default="http://127.0.0.1:8000", help="Base URL (default: http://127.0.0.1:8000)")
    args = parser.parse_args()

    clean_base_url = args.base_url.rstrip("/")

    print("=" * 95)
    print(" VEYRA AUTHORITATIVE 16-DAY TRAJECTORY VERIFICATION UTILITY")
    print(f" Endpoint: {clean_base_url}/v1/dashboard/intelligence (mode=full_16d)")
    print(f" Target Location: {args.location} | Variable: {args.variable}")
    print("=" * 95)

    # 1. Health Probe
    print(f"\n[1/3] Probing service health at {clean_base_url}/v1/health...")
    try:
        req = urllib.request.Request(f"{clean_base_url}/v1/health")
        with urllib.request.urlopen(req, timeout=10) as resp:
            health = json.loads(resp.read().decode("utf-8"))
            print(f"  [+] Service Health: {health.get('status')} (service: {health.get('service')}, version: {health.get('version')})")
    except Exception as e:
        print(f"  [-] Failed connecting to Veyra backend at {clean_base_url}: {e}")
        print("  Please ensure the FastAPI backend is running via:")
        print("    python -m uvicorn backend.app.main:app --port 8000")
        sys.exit(1)

    # 2. Trajectory Request
    print("\n[2/3] Requesting authoritative 16-day trajectory from /v1/dashboard/intelligence...")
    payload = json.dumps({
        "location": args.location,
        "variable": args.variable,
        "mode": "full_16d"
    }).encode("utf-8")

    t0 = time.time()
    try:
        req = urllib.request.Request(
            f"{clean_base_url}/v1/dashboard/intelligence",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            dash_resp = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  [-] Trajectory request failed: {e}")
        sys.exit(1)

    elapsed_ms = round((time.time() - t0) * 1000, 1)
    print(f"  [+] Received response in {elapsed_ms}ms with status: {dash_resp.get('status')}")

    loc = dash_resp.get("location")
    if loc:
        print(f"  Resolved Station : {loc.get('resolved_name')} ({loc.get('latitude')}, {loc.get('longitude')})")
    print(f"  Forecast Issue   : {dash_resp.get('issue_time')}")

    timeline = dash_resp.get("timeline") or []
    if not timeline:
        print("  [-] Warning: No timeline points returned by backend!")
        sys.exit(1)

    print(f"\nAuthoritative Timeline Trajectory ({len(timeline)} Points):")
    print("-" * 120)
    print(f"{'Day':<5} | {'Lead':<5} | {'Valid Time':<20} | {'P(Bust) Raw':<12} | {'P(Bust)%':<8} | {'Risk Tier':<9} | {'Trust State':<16} | {'Abstain':<7} | {'Calibration':<11} | {'Scope':<11}")
    print("-" * 120)

    valid_prob_count = 0
    abstained_count = 0
    unique_probs = set()

    for pt in timeline:
        actual_lead = pt.get("lead_hours", 0)
        day_calc = round(actual_lead / 24.0, 1)
        valid_time = pt.get("valid_time", "")
        raw_prob = pt.get("bust_probability")

        if raw_prob is not None:
            prob_raw_str = f"{raw_prob:.6f}"
            prob_pct_str = f"{raw_prob * 100:.2f}%"
            valid_prob_count += 1
            unique_probs.add(raw_prob)
        else:
            prob_raw_str = "ABSTAIN"
            prob_pct_str = "ABSTAIN"
            abstained_count += 1

        risk_str = pt.get("risk_level") or "NULL"
        trust_str = pt.get("trust_state") or "NULL"
        abstain_str = "TRUE" if pt.get("abstain") else "FALSE"
        cal_str = pt.get("calibration_status") or "UNAVAILABLE"
        scope_str = "CERTIFIED" if pt.get("is_certified_horizon") else "OPERATIONAL"

        print(f"{day_calc:<5} | {actual_lead:<4}h | {valid_time:<20} | {prob_raw_str:<12} | {prob_pct_str:<8} | {risk_str:<9} | {trust_str:<16} | {abstain_str:<7} | {cal_str:<11} | {scope_str:<11}")

    print("-" * 120)
    print("Summary Diagnostics:")
    print(f"  Total Requested Horizons : {len(timeline)}")
    print(f"  Valid Non-Null Points    : {valid_prob_count}")
    print(f"  Abstained Points         : {abstained_count}")
    print(f"  Distinct Calibrated Probs: {len(unique_probs)}")

    summary = dash_resp.get("summary")
    if summary:
        max_p = summary.get("max_bust_probability")
        max_p_str = f"{max_p * 100:.2f}%" if max_p is not None else "NULL"
        mean_p = summary.get("mean_bust_probability")
        mean_p_str = f"{mean_p * 100:.2f}%" if mean_p is not None else "NULL"
        print(f"  Peak Bust Probability   : {max_p_str}")
        print(f"  Peak Risk Level          : {summary.get('max_risk_level') or 'NULL'}")
        lead = summary.get('max_risk_lead_hours')
        print(f"  Peak Risk Horizon        : {str(lead) + 'h' if lead else 'NULL'}")
        print(f"  Mean Bust Probability    : {mean_p_str}")
        print(f"  Elevated Risk Horizons   : {summary.get('elevated_risk_points', 0)} / {summary.get('total_points', 0)}")
    print("=" * 95)

    # 3. Contract Safety Verification
    print("\n[3/3] Verifying Contract Safety: Testing unsupported 'lead_hours' on /v1/predict...")
    bad_payload = json.dumps({
        "location": args.location,
        "lead_hours": 48,
        "variable": args.variable
    }).encode("utf-8")

    try:
        bad_req = urllib.request.Request(
            f"{clean_base_url}/v1/predict",
            data=bad_payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(bad_req, timeout=10) as _:
            print("  [-] CRITICAL DEFECT: Backend accepted unsupported 'lead_hours' field with 200 OK!")
            sys.exit(1)
    except urllib.error.HTTPError as he:
        if he.code == 422:
            print("  [+] PASS: Backend strictly rejected unsupported 'lead_hours' with HTTP 422 Unprocessable Entity.")
        else:
            print(f"  [!] Unexpected status code: {he.code} (Expected 422)")
    except Exception as ex:
        print(f"  [!] Error checking contract: {ex}")

    print("\n[+] 16-DAY TRAJECTORY VERIFICATION COMPLETED SUCCESSFULLY.")
    print("=" * 95)


if __name__ == "__main__":
    main()
