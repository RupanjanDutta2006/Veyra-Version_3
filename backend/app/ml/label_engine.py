"""Bust Label Engine & Sensitivity Verification Module.

Implements the official SIH26079 Bust Definition & Labeling Protocol (§8.1, §8.2):
- Primary bust label: B = 1 if E_norm > Q_0.95^train(tau, v, R, season)
- Robust error normalization: E_norm = (E - median(E)) / (MAD(E) + eps)
- Sensitivity reruns at q90, q97.5, and q99
- Near-threshold ambiguity flag for gray-band cases
- Continuous normalized error and severity classification (low, moderate, severe)
- Versioned label metadata persistence (label_version: "v2.0-q95-mad")
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

CURRENT_LABEL_VERSION = "v2.0-q95-mad"
DEFAULT_SENSITIVITY_QUANTILES = [0.90, 0.95, 0.975, 0.99]
DEFAULT_PRIMARY_QUANTILE = 0.95
MIN_SAMPLES_FOR_STRATIFICATION = 10
AMBIGUITY_TOLERANCE_MAD = 0.25  # Near threshold if within +/- 0.25 MAD


def assign_lead_bin(lead_hours: Union[int, float, pd.Series]) -> Union[str, pd.Series]:
    """Categorize continuous lead hours into medium-range operational lead bins."""
    bins = [-1, 24, 72, 144, 240, 9999]
    labels = ["day1", "day2_3", "day4_6", "day7_10", "day10_plus"]
    if isinstance(lead_hours, (pd.Series, np.ndarray)):
        return pd.cut(lead_hours, bins=bins, labels=labels).astype(str)
    for i in range(len(bins) - 1):
        if bins[i] < lead_hours <= bins[i + 1]:
            return labels[i]
    return "day10_plus"


def compute_mad(values: np.ndarray, scale: float = 1.4826) -> float:
    """Compute Median Absolute Deviation (MAD) with normal distribution scaling.
    
    scale=1.4826 makes MAD an asymptotically consistent estimator for the standard
    deviation of a normal distribution.
    """
    if len(values) == 0:
        return 0.0
    med = np.median(values)
    mad = np.median(np.abs(values - med))
    return float(mad * scale)


@dataclass
class SingleBustEvaluation:
    """Evaluation result for a single forecast error instance."""

    is_bust: int  # 1 for bust, 0 for no-bust at primary quantile
    primary_quantile: float
    threshold_value: float
    normalized_error: float
    severity: str  # 'low', 'moderate', 'severe'
    ambiguity_flag: bool  # True if in gray-band near threshold
    sensitivity_labels: Dict[str, int]  # {'q90': 1, 'q95': 1, 'q975': 0, 'q99': 0}
    label_version: str = CURRENT_LABEL_VERSION
    details: Dict[str, Any] = field(default_factory=dict)


class BustLabelEngine:
    """Authoritative Bust Labeling Engine with Sensitivity, Ambiguity & Severity Support.
    
    Follows §8.1 & §8.2 of SIH26079 Specification:
    - Normalizes error via Median & MAD fit exclusively on training data.
    - Generates binary labels at primary quantile Q_0.95.
    - Evaluates sensitivity across Q_0.90, Q_0.95, Q_0.975, Q_0.99.
    - Identifies gray-band ambiguity (near threshold within +/-0.25 MAD or between q90 and q95).
    - Classifies severity:
        - 'low': below threshold (E_norm < Q_thresh)
        - 'moderate': Q_thresh <= E_norm <= 1.5 * Q_thresh
        - 'severe': E_norm > 1.5 * Q_thresh
    """

    def __init__(
        self,
        primary_quantile: float = DEFAULT_PRIMARY_QUANTILE,
        sensitivity_quantiles: Optional[List[float]] = None,
        min_samples_per_stratum: int = MIN_SAMPLES_FOR_STRATIFICATION,
        error_column: str = "forecast_abs_error",
        label_version: str = CURRENT_LABEL_VERSION,
        ambiguity_mad_tolerance: float = AMBIGUITY_TOLERANCE_MAD,
    ):
        self.primary_quantile = primary_quantile
        self.sensitivity_quantiles = sorted(list(set((sensitivity_quantiles or DEFAULT_SENSITIVITY_QUANTILES) + [primary_quantile])))
        self.min_samples_per_stratum = min_samples_per_stratum
        self.error_column = error_column
        self.label_version = label_version
        self.ambiguity_mad_tolerance = ambiguity_mad_tolerance
        self.thresholds_: Dict[str, Any] = {}
        self.is_fitted_ = False

    def fit(self, df_train: pd.DataFrame) -> "BustLabelEngine":
        """Fit conditional error distributions, MAD, and quantiles on training data."""
        if df_train.empty:
            raise ValueError("Cannot fit BustLabelEngine on an empty DataFrame.")
        if self.error_column not in df_train.columns:
            raise ValueError(f"Required error column '{self.error_column}' not found in training DataFrame.")

        df = df_train.copy()
        if "lead_bin" not in df.columns and "lead_hours" in df.columns:
            df["lead_bin"] = assign_lead_bin(df["lead_hours"])

        raw_errors = df[self.error_column].dropna().to_numpy()
        global_median = float(np.median(raw_errors))
        global_mad = float(compute_mad(raw_errors))
        eps = 1e-6

        # Normalized errors
        df["_e_norm"] = (df[self.error_column] - global_median) / (global_mad + eps)

        all_quantiles = self.sensitivity_quantiles

        fitted_dict: Dict[str, Any] = {
            "meta": {
                "label_version": self.label_version,
                "training_sample_count": len(df),
                "primary_quantile": self.primary_quantile,
                "sensitivity_quantiles": self.sensitivity_quantiles,
                "error_column": self.error_column,
                "global_median": global_median,
                "global_mad": global_mad,
                "ambiguity_mad_tolerance": self.ambiguity_mad_tolerance,
            },
            "global_thresholds": {
                f"q_{int(q*1000)}": float(df["_e_norm"].quantile(q)) for q in all_quantiles
            },
            "global_raw_thresholds": {
                f"q_{int(q*1000)}": float(df[self.error_column].quantile(q)) for q in all_quantiles
            },
            "variable_stats": {},
            "stratified_stats": {},
        }

        # 1. Per-variable distributions
        if "variable" in df.columns:
            for var, group in df.groupby("variable"):
                v_errs = group[self.error_column].dropna().to_numpy()
                if len(v_errs) >= self.min_samples_per_stratum:
                    v_med = float(np.median(v_errs))
                    v_mad = float(compute_mad(v_errs))
                    v_norm = (v_errs - v_med) / (v_mad + eps)
                    fitted_dict["variable_stats"][str(var)] = {
                        "count": len(v_errs),
                        "median": v_med,
                        "mad": v_mad,
                        "thresholds_norm": {f"q_{int(q*1000)}": float(np.percentile(v_norm, q * 100)) for q in all_quantiles},
                        "thresholds_raw": {f"q_{int(q*1000)}": float(np.percentile(v_errs, q * 100)) for q in all_quantiles},
                    }

        # 2. Stratified (location + variable + lead_bin)
        grouping_cols = ["location", "variable", "lead_bin"]
        available_cols = [c for c in grouping_cols if c in df.columns]

        if len(available_cols) == 3:
            for (loc, var, lbin), group in df.groupby(available_cols):
                s_errs = group[self.error_column].dropna().to_numpy()
                if len(s_errs) >= self.min_samples_per_stratum:
                    stratum_key = f"{loc}__{var}__{lbin}"
                    s_med = float(np.median(s_errs))
                    s_mad = float(compute_mad(s_errs))
                    s_norm = (s_errs - s_med) / (s_mad + eps)
                    fitted_dict["stratified_stats"][stratum_key] = {
                        "count": len(s_errs),
                        "median": s_med,
                        "mad": s_mad,
                        "thresholds_norm": {f"q_{int(q*1000)}": float(np.percentile(s_norm, q * 100)) for q in all_quantiles},
                        "thresholds_raw": {f"q_{int(q*1000)}": float(np.percentile(s_errs, q * 100)) for q in all_quantiles},
                    }

        self.thresholds_ = fitted_dict
        self.is_fitted_ = True
        return self

    def _lookup_stats(self, loc: Optional[str], var: Optional[str], lbin: Optional[str]) -> Tuple[float, float, Dict[str, float], Dict[str, float]]:
        """Look up median, mad, normalized thresholds and raw thresholds using fallback hierarchy."""
        stratum_key = f"{loc}__{var}__{lbin}"
        if stratum_key in self.thresholds_.get("stratified_stats", {}):
            s = self.thresholds_["stratified_stats"][stratum_key]
            return s["median"], s["mad"], s["thresholds_norm"], s["thresholds_raw"]

        if var and var in self.thresholds_.get("variable_stats", {}):
            s = self.thresholds_["variable_stats"][var]
            return s["median"], s["mad"], s["thresholds_norm"], s["thresholds_raw"]

        # Global fallback
        meta = self.thresholds_["meta"]
        return meta["global_median"], meta["global_mad"], self.thresholds_["global_thresholds"], self.thresholds_["global_raw_thresholds"]

    def evaluate_single(
        self,
        absolute_error: float,
        variable: Optional[str] = None,
        location: Optional[str] = None,
        lead_hours: int = 24,
    ) -> SingleBustEvaluation:
        """Evaluate a single error observation against fitted training thresholds."""
        if not self.is_fitted_:
            raise RuntimeError("BustLabelEngine must be fitted before calling evaluate_single().")

        lbin = assign_lead_bin(lead_hours)
        med, mad, norm_thresh, raw_thresh = self._lookup_stats(location, variable, lbin)

        eps = 1e-6
        e_norm = (absolute_error - med) / (mad + eps)

        q_key = f"q_{int(self.primary_quantile*1000)}"
        q_primary_norm = norm_thresh[q_key]
        q_primary_raw = raw_thresh[q_key]

        is_bust = 1 if e_norm >= q_primary_norm else 0

        # Sensitivity labels
        sensitivity_labels = {}
        for q in self.sensitivity_quantiles:
            k = f"q_{int(q*1000)}"
            q_suffix = str(int(q * 1000)).rstrip("0")
            sensitivity_labels[f"q{q_suffix}"] = 1 if e_norm >= norm_thresh[k] else 0

        # Ambiguity flag: within +/- ambiguity_mad_tolerance around threshold, or between q90 and q95
        q90_norm = norm_thresh.get("q_900", q_primary_norm - self.ambiguity_mad_tolerance)
        in_gray_zone = (e_norm >= q90_norm) and (e_norm < q_primary_norm)
        near_threshold = abs(e_norm - q_primary_norm) <= self.ambiguity_mad_tolerance
        ambiguity_flag = bool(in_gray_zone or near_threshold)

        # Severity classification (§8.2: low, moderate, severe)
        if e_norm < q_primary_norm:
            severity = "low"
        elif e_norm <= 1.5 * q_primary_norm:
            severity = "moderate"
        else:
            severity = "severe"

        return SingleBustEvaluation(
            is_bust=is_bust,
            primary_quantile=self.primary_quantile,
            threshold_value=q_primary_raw,
            normalized_error=round(float(e_norm), 4),
            severity=severity,
            ambiguity_flag=ambiguity_flag,
            sensitivity_labels=sensitivity_labels,
            label_version=self.label_version,
            details={
                "variable": variable,
                "location": location,
                "lead_bin": lbin,
                "median": med,
                "mad": mad,
                "norm_threshold": q_primary_norm,
            },
        )

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply fitted thresholds to generate bust labels, sensitivity columns, ambiguity, and severity."""
        if not self.is_fitted_:
            raise RuntimeError("BustLabelEngine must be fitted on training data before transform().")

        df_out = df.copy()
        if "lead_bin" not in df_out.columns and "lead_hours" in df_out.columns:
            df_out["lead_bin"] = assign_lead_bin(df_out["lead_hours"])

        q_key = f"q_{int(self.primary_quantile*1000)}"
        eps = 1e-6

        # Vectorized or row-wise evaluation
        norm_errors = []
        applied_thresholds = []
        primary_busts = []
        ambiguity_flags = []
        severities = []
        sensitivity_cols = {f"bust_label_q{str(int(q*1000)).rstrip('0')}": [] for q in self.sensitivity_quantiles}

        for _, row in df_out.iterrows():
            loc = row.get("location")
            var = row.get("variable")
            lbin = row.get("lead_bin") or assign_lead_bin(row.get("lead_hours", 0))
            abs_err = row[self.error_column]

            med, mad, norm_thresh, raw_thresh = self._lookup_stats(loc, var, lbin)
            e_norm = (abs_err - med) / (mad + eps)
            norm_errors.append(e_norm)

            primary_thresh_raw = raw_thresh[q_key]
            primary_thresh_norm = norm_thresh[q_key]
            applied_thresholds.append(primary_thresh_raw)

            is_b = 1 if e_norm >= primary_thresh_norm else 0
            primary_busts.append(is_b)

            # Ambiguity flag
            q90_norm = norm_thresh.get("q_900", primary_thresh_norm - self.ambiguity_mad_tolerance)
            is_ambig = (e_norm >= q90_norm and e_norm < primary_thresh_norm) or (abs(e_norm - primary_thresh_norm) <= self.ambiguity_mad_tolerance)
            ambiguity_flags.append(bool(is_ambig))

            # Severity
            if e_norm < primary_thresh_norm:
                sev = "low"
            elif e_norm <= 1.5 * primary_thresh_norm:
                sev = "moderate"
            else:
                sev = "severe"
            severities.append(sev)

            # Sensitivity
            for q in self.sensitivity_quantiles:
                k = f"q_{int(q*1000)}"
                col_name = f"bust_label_q{str(int(q*1000)).rstrip('0')}"
                sensitivity_cols[col_name].append(1 if e_norm >= norm_thresh[k] else 0)

        df_out["normalized_error"] = norm_errors
        df_out["bust_threshold"] = applied_thresholds
        df_out["bust_label"] = primary_busts
        df_out["is_ambiguous_zone"] = ambiguity_flags
        df_out["ambiguity_flag"] = ambiguity_flags
        df_out["severity"] = severities
        df_out["label_version"] = self.label_version

        for col_name, values in sensitivity_cols.items():
            df_out[col_name] = values

        return df_out

    def fit_transform(self, df_train: pd.DataFrame) -> pd.DataFrame:
        """Fit on training data and return transformed DataFrame."""
        return self.fit(df_train).transform(df_train)

    def save_thresholds(self, path: Union[str, Path]) -> None:
        """Persist fitted thresholds to a JSON file."""
        if not self.is_fitted_:
            raise RuntimeError("Engine has not been fitted.")
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(self.thresholds_, f, indent=2)

    def load_thresholds(self, path: Union[str, Path]) -> "BustLabelEngine":
        """Load frozen thresholds from a JSON file."""
        p = Path(path)
        with open(p, "r", encoding="utf-8") as f:
            self.thresholds_ = json.load(f)
        meta = self.thresholds_["meta"]
        self.primary_quantile = meta["primary_quantile"]
        self.sensitivity_quantiles = meta["sensitivity_quantiles"]
        self.error_column = meta["error_column"]
        self.label_version = meta.get("label_version", CURRENT_LABEL_VERSION)
        self.ambiguity_mad_tolerance = meta.get("ambiguity_mad_tolerance", AMBIGUITY_TOLERANCE_MAD)
        self.is_fitted_ = True
        return self
