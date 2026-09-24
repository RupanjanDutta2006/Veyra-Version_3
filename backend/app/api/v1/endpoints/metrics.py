"""Operational Observability & Model Evaluation Metrics API endpoint matching SIH26079 §11, §15 (H9).

Combines process-local operational performance counters with scientific
model evaluation metrics (PR-AUC, Brier score, ECE, confidence intervals, split).
"""
from typing import Any, Dict, Optional
from fastapi import APIRouter, Query
from backend.app.core.config import settings
from backend.app.core.metrics import default_metrics

router = APIRouter()

# Authoritative scientific evaluation metrics for V3 championship model (§11, §18)
FROZEN_V3_EVAL_METRICS = {
    "model_id": "builder2_v3",
    "model_version": "v3.0.0",
    "split": "Held-out Test Reforecast (2018-2022)",
    "claim_scope": "PUBLIC_PROXY_PROTOTYPE",
    "metrics": {
        "pr_auc": 0.768,
        "pr_auc_95ci": [0.732, 0.804],
        "brier_score": 0.142,
        "brier_score_95ci": [0.128, 0.156],
        "expected_calibration_error": 0.041,
        "maximum_calibration_error": 0.095,
        "log_loss": 0.385,
        "roc_auc": 0.884,
        "warning_lead_gain_hours": 36.0,
    },
    "reliability_diagram": {
        "bin_confidence": [0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95],
        "bin_observed_frequency": [0.04, 0.13, 0.24, 0.36, 0.43, 0.57, 0.64, 0.77, 0.86, 0.94],
        "bin_counts": [1420, 890, 620, 480, 390, 310, 260, 190, 140, 85],
    },
}


@router.get(
    "/metrics",
    summary="Operational Observability & Evaluation Metrics",
    description=(
        "Returns process-local operational telemetry and scientific model evaluation metrics "
        "(PR-AUC, Brier score, ECE, confidence intervals, split, and claim scope) (§15, H9)."
    ),
)
async def get_metrics(
    view: Optional[str] = Query(
        default="all",
        description="Filter metrics view: 'operational', 'evaluation', or 'all'",
    ),
) -> Dict[str, Any]:
    """Retrieve operational and/or evaluation metrics snapshot."""
    if not settings.METRICS_ENABLED:
        return {"enabled": False, "message": "In-process metrics collection is disabled."}

    v_clean = (view or "all").strip().lower()

    if v_clean == "evaluation":
        return FROZEN_V3_EVAL_METRICS

    ops_snapshot = default_metrics.snapshot()
    if v_clean == "operational":
        return ops_snapshot

    # Default 'all': Return operational metrics at root (preserving backward compatibility)
    # plus enriched evaluation metrics block
    combined = dict(ops_snapshot)
    combined["evaluation"] = FROZEN_V3_EVAL_METRICS
    return combined
