"""FSS-Style Neighborhood and Object-Aware Spatial Bust Verification Module.

Implements the official SIH26079 Spatial Bust Protocol (§8.2):
- Fractions Skill Score (FSS) neighborhood evaluation
- Object-aware spatial displacement evaluation (centroid displacement, area fraction, IoU)
- Spatial displacement tolerance to avoid penalizing near-miss forecasts as total busts
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np


@dataclass
class SpatialBustResult:
    """Standardized output from spatial bust evaluation."""

    is_spatial_bust: int  # 1 for spatial bust, 0 for acceptable forecast
    fss_score: float  # Fractions Skill Score in [0, 1]
    fss_target: float  # Target FSS threshold (e.g. 0.5 or 0.5 + f_ref/2)
    mean_centroid_displacement_km: float  # Distance between forecast and reference objects
    object_overlap_iou: float  # Jaccard / IoU index
    forecast_area_fraction: float  # Fraction of grid exceeding threshold in forecast
    reference_area_fraction: float  # Fraction of grid exceeding threshold in reference
    displacement_mitigated: bool  # True if small displacement prevented false bust classification
    details: Dict[str, Any] = field(default_factory=dict)


def compute_neighborhood_fractions_2d(
    binary_field: np.ndarray,
    window_size: int = 5,
) -> np.ndarray:
    """Compute neighborhood fraction for each grid point using a 2D moving window.
    
    Args:
        binary_field: 2D binary numpy array (1 where value >= threshold, 0 otherwise).
        window_size: Odd integer neighborhood box width/height in grid cells.
        
    Returns:
        2D numpy array with neighborhood fraction values in [0, 1].
    """
    if window_size <= 1:
        return binary_field.astype(float)
    if window_size % 2 == 0:
        window_size += 1  # Force odd window size for symmetric centering

    pad = window_size // 2
    padded = np.pad(binary_field.astype(float), pad, mode="constant", constant_values=0.0)

    # 2D integral image (cumulative sum) for O(1) boxcar filtering
    integral = np.pad(padded.cumsum(axis=0).cumsum(axis=1), ((1, 0), (1, 0)), mode="constant", constant_values=0.0)

    h, w = binary_field.shape
    # Compute sum inside [r, r + window_size] x [c, c + window_size]
    r1, r2 = 0, h
    c1, c2 = 0, w

    y1 = np.arange(h)
    y2 = y1 + window_size
    x1 = np.arange(w)
    x2 = x1 + window_size

    # Grid evaluation using broadcasting
    sums = (
        integral[y2[:, None], x2[None, :]]
        - integral[y1[:, None], x2[None, :]]
        - integral[y2[:, None], x1[None, :]]
        + integral[y1[:, None], x1[None, :]]
    )
    return sums / (window_size * window_size)


def calculate_fss(
    forecast_field: np.ndarray,
    reference_field: np.ndarray,
    threshold: float,
    window_size: int = 5,
) -> float:
    """Calculate Fractions Skill Score (FSS) between forecast and reference fields.
    
    FSS = 1 - (MSE_window / MSE_ref)
    where:
      MSE_window = mean((F_frac - R_frac)^2)
      MSE_ref = mean(F_frac^2) + mean(R_frac^2)
    
    Returns:
      FSS score in [0.0, 1.0]. Perfect skill = 1.0; no skill = 0.0.
      If both fields are completely empty (no event anywhere), returns 1.0.
      If one field is completely empty and other has events, returns 0.0.
    """
    f_arr = np.asarray(forecast_field, dtype=float)
    r_arr = np.asarray(reference_field, dtype=float)

    if f_arr.shape != r_arr.shape:
        raise ValueError(f"Forecast shape {f_arr.shape} does not match reference shape {r_arr.shape}")

    # Binarize
    f_bin = (f_arr >= threshold).astype(float)
    r_bin = (r_arr >= threshold).astype(float)

    # Edge cases: identical fields
    if np.array_equal(f_bin, r_bin):
        return 1.0

    # Compute neighborhood fractions
    f_frac = compute_neighborhood_fractions_2d(f_bin, window_size=window_size)
    r_frac = compute_neighborhood_fractions_2d(r_bin, window_size=window_size)

    mse_window = float(np.mean((f_frac - r_frac) ** 2))
    mse_ref = float(np.mean(f_frac ** 2) + np.mean(r_frac ** 2))

    if mse_ref <= 1e-12:
        return 1.0 if mse_window <= 1e-12 else 0.0

    fss = 1.0 - (mse_window / mse_ref)
    return float(np.clip(fss, 0.0, 1.0))


def _find_connected_objects(binary_field: np.ndarray, min_size: int = 2) -> List[List[Tuple[int, int]]]:
    """Simple 8-connected component finder for 2D binary grid."""
    h, w = binary_field.shape
    visited = np.zeros((h, w), dtype=bool)
    objects: List[List[Tuple[int, int]]] = []

    for r in range(h):
        for c in range(w):
            if binary_field[r, c] and not visited[r, c]:
                # BFS/DFS to collect component
                comp: List[Tuple[int, int]] = []
                queue = [(r, c)]
                visited[r, c] = True

                while queue:
                    curr_r, curr_c = queue.pop(0)
                    comp.append((curr_r, curr_c))

                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = curr_r + dr, curr_c + dc
                            if 0 <= nr < h and 0 <= nc < w:
                                if binary_field[nr, nc] and not visited[nr, nc]:
                                    visited[nr, nc] = True
                                    queue.append((nr, nc))

                if len(comp) >= min_size:
                    objects.append(comp)

    return objects


def calculate_object_spatial_metrics(
    forecast_field: np.ndarray,
    reference_field: np.ndarray,
    threshold: float,
    grid_spacing_km: float = 25.0,  # e.g., 0.25 deg ~ 25-28 km
    min_object_size: int = 2,
) -> Dict[str, Any]:
    """Extract object-level spatial verification metrics (centroids, overlap, displacement)."""
    f_arr = np.asarray(forecast_field, dtype=float)
    r_arr = np.asarray(reference_field, dtype=float)

    f_bin = (f_arr >= threshold).astype(bool)
    r_bin = (r_arr >= threshold).astype(bool)

    total_cells = f_arr.size
    f_area_frac = float(np.sum(f_bin)) / total_cells
    r_area_frac = float(np.sum(r_bin)) / total_cells

    # Intersection over Union (IoU)
    intersection = np.logical_and(f_bin, r_bin).sum()
    union = np.logical_or(f_bin, r_bin).sum()
    iou = float(intersection / union) if union > 0 else 1.0 if (f_area_frac == 0 and r_area_frac == 0) else 0.0

    # Object identification
    f_objects = _find_connected_objects(f_bin, min_size=min_object_size)
    r_objects = _find_connected_objects(r_bin, min_size=min_object_size)

    f_centroids = []
    for obj in f_objects:
        coords = np.array(obj)
        cy, cx = coords[:, 0].mean(), coords[:, 1].mean()
        f_centroids.append((cy, cx))

    r_centroids = []
    for obj in r_objects:
        coords = np.array(obj)
        cy, cx = coords[:, 0].mean(), coords[:, 1].mean()
        r_centroids.append((cy, cx))

    # Calculate nearest centroid displacement distance
    displacements_km: List[float] = []
    if f_centroids and r_centroids:
        for f_cy, f_cx in f_centroids:
            min_d_cells = min(
                np.sqrt((f_cy - r_cy) ** 2 + (f_cx - r_cx) ** 2)
                for r_cy, r_cx in r_centroids
            )
            displacements_km.append(float(min_d_cells * grid_spacing_km))
    elif not f_centroids and not r_centroids:
        displacements_km = [0.0]
    else:
        # One has objects, the other has none -> penalty displacement
        displacements_km = [float(max(f_arr.shape) * grid_spacing_km)]

    mean_disp_km = float(np.mean(displacements_km)) if displacements_km else 0.0

    return {
        "forecast_area_fraction": round(f_area_frac, 4),
        "reference_area_fraction": round(r_area_frac, 4),
        "object_overlap_iou": round(iou, 4),
        "forecast_object_count": len(f_objects),
        "reference_object_count": len(r_objects),
        "mean_centroid_displacement_km": round(mean_disp_km, 2),
        "displacements_km": displacements_km,
    }


def evaluate_spatial_bust(
    forecast_field: np.ndarray,
    reference_field: np.ndarray,
    threshold: float,
    window_size: int = 5,
    grid_spacing_km: float = 25.0,
    fss_target: float = 0.50,
    displacement_tolerance_km: float = 75.0,  # ~3 grid cells at 25km
) -> SpatialBustResult:
    """Comprehensive spatial bust evaluation combining FSS and object displacement (§8.2).
    
    A forecast is classified as a spatial bust if:
      - FSS < fss_target AND
      - Not saved by small displacement tolerance (i.e., displacement > displacement_tolerance_km).
    """
    fss = calculate_fss(forecast_field, reference_field, threshold=threshold, window_size=window_size)
    obj_metrics = calculate_object_spatial_metrics(
        forecast_field, reference_field, threshold=threshold, grid_spacing_km=grid_spacing_km
    )

    f_area = obj_metrics["forecast_area_fraction"]
    r_area = obj_metrics["reference_area_fraction"]
    disp_km = obj_metrics["mean_centroid_displacement_km"]
    iou = obj_metrics["object_overlap_iou"]

    # Displacement mitigation logic (§8.2: "a forecast displaced by a small distance is not treated as a total failure")
    # If FSS is marginally below target but the event was predicted with matching size and centroid within tolerance:
    displacement_mitigated = False
    raw_bust = 1 if fss < fss_target else 0

    if raw_bust == 1:
        both_have_events = (f_area > 0.01) and (r_area > 0.01)
        area_ratio = min(f_area, r_area) / max(f_area, r_area) if max(f_area, r_area) > 0 else 0.0
        if both_have_events and disp_km <= displacement_tolerance_km and area_ratio >= 0.5:
            # Event was predicted accurately in magnitude and structure, just slightly displaced
            displacement_mitigated = True
            is_bust = 0
        else:
            is_bust = 1
    else:
        is_bust = 0

    return SpatialBustResult(
        is_spatial_bust=is_bust,
        fss_score=round(fss, 4),
        fss_target=fss_target,
        mean_centroid_displacement_km=disp_km,
        object_overlap_iou=iou,
        forecast_area_fraction=f_area,
        reference_area_fraction=r_area,
        displacement_mitigated=displacement_mitigated,
        details=obj_metrics,
    )
