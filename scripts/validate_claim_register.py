import argparse
import csv
import sys
import os

def validate_register(input_path, required_classes):
    print(f"Validating Claim Register at: {input_path}")
    if not os.path.exists(input_path):
        print(f"Error: File not found: {input_path}")
        return 1

    valid_classes = set(c.strip() for c in required_classes.split(","))
    required_columns = [
        "claim_id", "claim", "source_file", "code_path", "artifact_path",
        "test_command", "runtime_observation", "evidence_class",
        "current_status", "owner", "correction", "documentation_disposition"
    ]

    claims = []
    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for col in required_columns:
            if col not in reader.fieldnames:
                print(f"Error: Missing required column '{col}' in CSV.")
                return 1
        for row_idx, row in enumerate(reader, start=2):
            cid = row.get("claim_id", "").strip()
            eclass = row.get("evidence_class", "").strip()
            if not cid:
                print(f"Error: Row {row_idx} missing claim_id")
                return 1
            if eclass not in valid_classes:
                print(f"Error: Row {row_idx} ({cid}) has invalid evidence_class '{eclass}'. Must be one of {valid_classes}")
                return 1
            claims.append(row)

    if len(claims) == 0:
        print("Error: Claim register is empty!")
        return 1

    print(f"[PASS] Verified {len(claims)} claims across required evidence classes.")
    class_counts = {}
    for c in claims:
        e = c["evidence_class"]
        class_counts[e] = class_counts.get(e, 0) + 1
    for k, v in sorted(class_counts.items()):
        print(f"  - {k}: {v} claims")

    print("=== GATE P0-1 COMPULSORY CLAIM REGISTER VALIDATION PASSED ===")
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="manifests/claim_register.csv")
    parser.add_argument("--required-classes", default="REPRODUCED,SUPPORTED_BY_ARTIFACT,SUPPORTED_BY_CODE_ONLY,SUPPORTED_BY_TEST_FIXTURE_ONLY,DOCUMENTATION_ONLY,CONTRADICTED,UNVERIFIED")
    args = parser.parse_args()
    sys.exit(validate_register(args.input, args.required_classes))
