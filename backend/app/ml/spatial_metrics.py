"""Spatial and Object-Aware Forecast Verification Metrics (§18.1, File 084, File 087).

Implements spatial verification metrics for gridded bust forecasts:
- Fractions Skill Score (FSS) across multiple neighborhood scales (Roberts & Lean, 2008).
- Object Overlap (IoU / Jaccard Index) for segmented risk patches.
- Centroid displacement error (Haversine distance in km).
- Top-k regional recall (identifying highest risk stations/patches).
- Area fraction coverage and area error.
"""
from dataclasses import asdict, dataclass, field
import math
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from scipy.ndimage import uniform_filter


EARTH_RADIUS_KM = 6371.0


@dataclass
class SpatialMetricsReport:
    """Container for spatial and object-aware verification metrics."""

    fss_by_scale: dict[str, float]  # e.g. {"3x3": 0.82, "5x5": 0.89, "9x9": 0.94}
    mean_fss: float
    fss_useful_scale: Optional[str]  # Smallest scale where FSS >= 0.5 + f0/2
    object_iou: float
    centroid_error_km: Optional[float]
    top_k_recall: float
    k_value: int
    pred_area_fraction: float
    obs_area_fraction: float
    area_fraction_error: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "fss_by_scale": {k: round(v, 4) for k, v in self.fss_by_scale.items()},
            "mean_fss": round(self.mean_fss, 4),
            "fss_useful_scale": self.fss_useful_scale,
            "object_iou": round(self.object_iou, 4),
            "centroid_error_km": round(self.centroid_error_km, 2) if self.centroid_error_km is not None else None,
            "top_k_recall": round(self.top_k_recall, 4),
            "k_value": self.k_value,
            "pred_area_fraction": round(self.pred_area_fraction, 4),
            "obs_area_fraction": round(self.obs_area_fraction, 4),
            "area_fraction_error": round(self.area_fraction_error, 4),
        }


def compute_fss(
    forecast_field: np.ndarray,
    truth_field: np.ndarray,
    threshold: float = 0.5,
    window_size: int = 3,
) -> float:
    """Compute Fractions Skill Score (FSS) for a 2D forecast and truth field.

    FSS = 1 - (FBS / FBS_ref)
    where:
      FBS = (1 / N) * sum((O_ij - M_ij)^2)
      FBS_ref = (1 / N) * sum(O_ij^2 + M_ij^2)
      O_ij = fraction of observed events in window around (i, j)
      M_ij = fraction of modeled events in window around (i, j)

    Args:
        forecast_field: 2D array of predicted probabilities or continuous values.
        truth_field: 2D array of true labels or continuous verification values.
        threshold: Threshold to binarize fields into events (>= threshold).
        window_size: Odd integer neighborhood size (e.g. 3, 5, 9).

    Returns:
        FSS value in [0.0, 1.0]. Returns 1.0 if both fields have zero events.
    """
    f_arr = np.asarray(forecast_field, dtype=np.float64)
    t_arr = np.asarray(truth_field, dtype=np.float64)

    if f_arr.ndim != 2 or t_arr.ndim != 2:
        raise ValueError(f"FSS requires 2D arrays, got forecast ndim={f_arr.ndim}, truth ndim={t_arr.ndim}")
    if f_arr.shape != t_arr.shape:
        raise ValueError(f"Shape mismatch: forecast {f_arr.shape} != truth {t_arr.shape}")

    # Binarize fields
    bin_f = (f_arr >= threshold).astype(np.float64)
    bin_t = (t_arr >= threshold).astype(np.float64)

    total_pts = bin_f.size
    if total_pts == 0:
        return 1.0

    # If both fields are identical
    if np.array_equal(bin_f, bin_t):
        return 1.0

    # If neither field has any events
    if np.sum(bin_f) == 0 and np.sum(bin_t) == 0:
        return 1.0

    # Ensure window_size is positive and odd
    w = max(1, int(window_size))
    if w % 2 == 0:
        w += 1

    # Fractional fields via uniform_filter (equivalent to 2D moving average box)
    # Mode='constant', cval=0.0 to prevent wrapping at grid boundaries
    m_frac = uniform_filter(bin_f, size=w, mode="constant", cval=0.0)
    o_frac = uniform_filter(bin_t, size=w, mode="constant", cval=0.0)

    # Fractions Brier Score (FBS)
    fbs = float(np.mean((m_frac - o_frac) ** 2))
    # Reference FBS (worst case where events never overlap)
    fbs_ref = float(np.mean(m_frac**2 + o_frac**2))

    if fbs_ref == 0.0:
        return 1.0 if fbs == 0.0 else 0.0

    fss = 1.0 - (fbs / fbs_ref)
    return float(np.clip(fss, 0.0, 1.0))


def compute_object_iou(
    pred_mask: np.ndarray,
    obs_mask: np.ndarray,
    threshold: float = 0.5,
) -> float:
    """Compute Intersection over Union (IoU / Jaccard Index) for binary risk masks.

    Args:
        pred_mask: Predicted boolean or probability mask.
        obs_mask: Observed boolean or ground truth mask.
        threshold: Threshold for binarizing float masks.

    Returns:
        IoU in [0.0, 1.0].
    """
    p = np.asarray(pred_mask) >= threshold
    o = np.asarray(obs_mask) >= threshold

    intersection = int(np.sum(p & o))
    union = int(np.sum(p | o))

    if union == 0:
        return 1.0  # Perfect agreement on empty field
    return float(intersection / union)


def compute_haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Compute great-circle distance between two geographic coordinates in kilometers."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_KM * c


def compute_centroid(
    mask: np.ndarray,
    lats: Optional[np.ndarray] = None,
    lons: Optional[np.ndarray] = None,
) -> Optional[Tuple[float, float]]:
    """Compute centroid coordinate (lat, lon) or (row, col) of positive mask pixels."""
    coords = np.argwhere(mask)
    if len(coords) == 0:
        return None

    if lats is not None and lons is not None:
        mean_lat = float(np.mean(lats[coords[:, 0]]))
        mean_lon = float(np.mean(lons[coords[:, 1]]))
        return mean_lat, mean_lon
    else:
        mean_r = float(np.mean(coords[:, 0]))
        mean_c = float(np.mean(coords[:, 1]))
        return mean_r, mean_c


def compute_centroid_error(
    pred_mask: np.ndarray,
    obs_mask: np.ndarray,
    lats: Optional[np.ndarray] = None,
    lons: Optional[np.ndarray] = None,
    threshold: float = 0.5,
) -> Optional[float]:
    """Compute displacement error between predicted and observed event centroids.

    Returns:
        Distance in kilometers if lats/lons provided, else Euclidean grid distance.
        Returns None if either mask has no positive pixels.
    """
    p = np.asarray(pred_mask) >= threshold
    o = np.asarray(obs_mask) >= threshold

    c_pred = compute_centroid(p, lats=lats, lons=lons)
    c_obs = compute_centroid(o, lats=lats, lons=lons)

    if c_pred is None or c_obs is None:
        return None

    if lats is not None and lons is not None:
        return compute_haversine_distance(c_pred[0], c_pred[1], c_obs[0], c_obs[1])
    else:
        return math.sqrt((c_pred[0] - c_obs[0]) ** 2 + (c_pred[1] - c_obs[1]) ** 2)


def compute_top_k_spatial_recall(
    y_prob: np.ndarray,
    y_true: np.ndarray,
    k: int = 5,
) -> float:
    """Compute Top-k regional recall (§18.1).

    Given N spatial units (stations or grid patches) with predicted bust probabilities
    and actual binary bust outcomes:
    Top-k Recall = (actual busts in top k highest-probability regions) / (total actual busts).

    Args:
        y_prob: Array of predicted probabilities for each location.
        y_true: Array of true binary labels (1=bust, 0=non-bust).
        k: Number of top-ranked locations to consider.

    Returns:
        Recall score in [0.0, 1.0]. Returns 1.0 if total actual busts is 0.
    """
    prob = np.asarray(y_prob, dtype=np.float64)
    true = np.asarray(y_true, dtype=np.int64)

    total_busts = int(np.sum(true == 1))
    if total_busts == 0:
        return 1.0

    k_actual = min(len(prob), max(1, int(k)))
    # Indices of top-k highest probabilities
    top_k_indices = np.argsort(prob)[::-1][:k_actual]
    busts_in_top_k = int(np.sum(true[top_k_indices] == 1))

    return float(busts_in_top_k / total_busts)


def compute_area_fraction_error(
    pred_mask: np.ndarray,
    obs_mask: np.ndarray,
    threshold: float = 0.5,
) -> Tuple[float, float, float]:
    """Compute predicted area fraction, observed area fraction, and absolute error.

    Returns:
        (pred_fraction, obs_fraction, abs_error)
    """
    p = np.asarray(pred_mask) >= threshold
    o = np.asarray(obs_mask) >= threshold

    total_pts = p.size
    if total_pts == 0:
        return 0.0, 0.0, 0.0

    p_frac = float(np.sum(p) / total_pts)
    o_frac = float(np.sum(o) / total_pts)
    err = abs(p_frac - o_frac)
    return p_frac, o_frac, err


def evaluate_spatial_grid(
    pred_field: np.ndarray,
    obs_field: np.ndarray,
    threshold: float = 0.5,
    window_sizes: Optional[list[int]] = None,
    k: int = 5,
    lats: Optional[np.ndarray] = None,
    lons: Optional[np.ndarray] = None,
) -> SpatialMetricsReport:
    """High-level spatial and object-aware evaluation suite per §18.1."""
    if window_sizes is None:
        window_sizes = [3, 5, 9]

    fss_dict: dict[str, float] = {}
    f0 = float(np.mean(np.asarray(obs_field) >= threshold))
    useful_criterion = 0.5 + (f0 / 2.0)
    useful_scale: Optional[str] = None

    for w in window_sizes:
        scale_key = f"{w}x{w}"
        score = compute_fss(pred_field, obs_field, threshold=threshold, window_size=w)
        fss_dict[scale_key] = score
        if useful_scale is None and score >= useful_criterion:
            useful_scale = scale_key

    mean_fss = float(np.mean(list(fss_dict.values()))) if fss_dict else 0.0
    iou = compute_object_iou(pred_field, obs_field, threshold=threshold)
    c_err = compute_centroid_error(pred_field, obs_field, lats=lats, lons=lons, threshold=threshold)
    top_k = compute_top_k_spatial_recall(pred_field.flatten(), obs_field.flatten(), k=k)
    p_frac, o_frac, a_err = compute_area_fraction_error(pred_field, obs_field, threshold=threshold)

    return SpatialMetricsReport(
        fss_by_scale=fss_dict,
        mean_fss=mean_fss,
        fss_useful_scale=useful_scale,
        object_iou=iou,
        centroid_error_km=c_err,
        top_k_recall=top_k,
        k_value=k,
        pred_area_fraction=p_frac,
        obs_area_fraction=o_frac,
        area_fraction_error=a_err,
    )
