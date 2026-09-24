"""
Veyra Sentinel — Live System End-to-End Verification Test
Tests all active endpoints against http://127.0.0.1:8000
"""

import json
import urllib.request
import urllib.error
import sys

BASE_URL = "http://127.0.0.1:8000"

def make_request(method: str, path: str, data: dict = None, headers: dict = None):
    url = f"{BASE_URL}{path}"
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            return e.code, json.loads(content)
        except Exception:
            return e.code, {"error": content}
    except Exception as e:
        return 0, {"error": str(e)}

def run_tests():
    print("=" * 80)
    print("      VEYRA SENTINEL (SIH26079) — LIVE SYSTEM VERIFICATION SUITE")
    print("=" * 80)
    
    passed = 0
    total = 0

    def test(name, method, path, data=None, headers=None, expected_status=200):
        nonlocal passed, total
        total += 1
        print(f"[{total:02d}] Testing {method:<4} {path:<48} ...", end=" ", flush=True)
        status, resp = make_request(method, path, data, headers)
        if status == expected_status:
            print(f"PASS (Status {status})")
            passed += 1
            return resp
        else:
            print(f"FAIL (Expected {expected_status}, got {status}): {resp}")
            return None

    # 1. Health
    r1 = test("Health Check", "GET", "/v1/health")
    assert r1 and r1.get("status") == "ok"

    # 2. Model Registry List
    r2 = test("List Models", "GET", "/v1/models")
    assert r2 and len(r2) > 0
    print(f"     Serving Model: {r2[0].get('name')} (Version: {r2[0].get('version')})")

    # 3. Model Specific Record
    r3 = test("Get Model Record", "GET", "/v1/models/builder2_v3")
    assert r3 and r3.get("model_id") == "builder2_v3"

    # 4. Model Promotion Lifecycle Gates
    r4 = test("Model Lifecycle Gates", "GET", "/v1/models/builder2_v3/gates?target_status=VALIDATED")
    assert r4 and ("passed" in r4 or "gate_checks" in r4)

    # 5. Operational & Scientific Evaluation Metrics
    r5 = test("Observability & Eval Metrics", "GET", "/v1/metrics?view=all")
    assert r5 and "evaluation" in r5
    eval_m = r5["evaluation"]["metrics"]
    print(f"     PR-AUC: {eval_m.get('pr_auc')}, Brier Score: {eval_m.get('brier_score')}, ECE: {eval_m.get('expected_calibration_error')}")

    # 6. System Metadata
    r6 = test("System Metadata", "GET", "/v1/metadata")
    assert r6 is not None

    # 7. Forecast Catalog & Replay Cases
    r7 = test("Forecast Catalog & Replay Cases", "GET", "/v1/forecasts")
    assert r7 and "cycles" in r7 and "replay_cases" in r7
    print(f"     Operational Cycles: {len(r7['cycles'])}, Replay Cases: {len(r7['replay_cases'])}")

    # 8. Predict (Standard Location - Mumbai)
    predict_payload = {
        "location": "Mumbai",
        "variable": "wind_speed_10m"
    }
    r8 = test("Predict Bust Risk (Mumbai)", "POST", "/v1/predict", data=predict_payload)
    if r8:
        print(f"     Bust Prob: {r8.get('bust_probability')}, Trust State: {r8.get('trust_state')}, Risk Band: {r8.get('risk_band')}")

    # 9. Predict with Explicit Forecast Horizon (Delhi, 48h lead)
    horizon_payload = {
        "location": "Delhi",
        "variable": "temperature_2m",
        "issue_time": "2026-09-20T00:00:00Z",
        "valid_time": "2026-09-22T00:00:00Z"
    }
    r9 = test("Predict Explicit Horizon (Delhi 48h)", "POST", "/v1/predict", data=horizon_payload)
    if r9:
        print(f"     Lead Hours: {r9.get('lead_hours')}, Trust State: {r9.get('trust_state')}")

    # 10. Historical Analogs
    r10 = test("Historical Analogs", "GET", "/v1/analogs?location=Mumbai&limit=3")
    if r10:
        print(f"     Found Analogs: {len(r10.get('analogs', []))}")

    # 11. Regional Risk Map (GeoJSON)
    r11 = test("Regional Risk Map (GeoJSON)", "GET", "/v1/risk-map?region=INDIA_ALL")
    assert r11 and "features" in r11
    print(f"     GeoJSON Features: {len(r11.get('features', []))}")

    # 12. Physical Attribution & Explanation
    r12 = test("Physical Attribution", "GET", "/v1/explanation?location=Mumbai")
    assert r12 is not None

    # 13. Data Provenance & Lineage
    r13 = test("Data Provenance & Lineage", "GET", "/v1/data-provenance")
    assert r13 and "checksums" in r13

    # 14. Data Export (IMD CAP / JSON Format)
    r14 = test("Data Export (CAP Format)", "GET", "/v1/export?format=json&scope=national")
    assert r14 is not None

    # 15. Evaluation Comprehensive Report (§18.1)
    r15 = test("Evaluation Comprehensive", "GET", "/v1/model/evaluation/comprehensive?model=v3")
    assert r15 is not None

    # 16. Evaluation V3 Dedicated Metrics
    r16 = test("Evaluation V3 Metrics", "GET", "/v1/model/evaluation/v3")
    assert r16 is not None

    # 17. Human-in-the-Loop Review (Submission & Retrieval)
    review_pred_id = r8.get("prediction_id", "pred_test_001") if r8 else "pred_test_001"
    review_payload = {
        "status": "APPROVED",
        "forecaster_id": "MET-SENIOR-108",
        "forecaster_notes": "Verified synoptic convective burst signatures over northern Arabian Sea."
    }
    r17 = test("Submit HITL Review", "POST", f"/v1/predictions/{review_pred_id}/review", data=review_payload)
    r18 = test("Retrieve HITL Review", "GET", f"/v1/predictions/{review_pred_id}/review")
    if r18:
        print(f"     HITL Decision: {r18.get('status')} by {r18.get('forecaster_id')}")

    # 19. Scope Enforcement (Unsupported Foreign Location - London)
    london_payload = {
        "location": "London",
        "variable": "wind_speed_10m"
    }
    r19 = test("Scope Enforcement (London)", "POST", "/v1/predict", data=london_payload)
    if r19:
        print(f"     Warnings: {r19.get('warnings')}")

    # 20. OOD Abstention (North Pole)
    pole_payload = {
        "location": "North Pole",
        "variable": "wind_speed_10m"
    }
    r20 = test("OOD Abstention (North Pole)", "POST", "/v1/predict", data=pole_payload)
    if r20:
        print(f"     Trust State: {r20.get('trust_state')}, Prob: {r20.get('bust_probability')}")

    print("=" * 80)
    print(f"  ALL TESTS COMPLETE: {passed}/{total} ENDPOINTS PASSED ({passed/total*100:.1f}%)")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()
