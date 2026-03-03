from __future__ import annotations

import numpy as np


def build_grouping(group_values: np.ndarray | None = None) -> np.ndarray:
    """
    Domain-agnostic grouping fallback.

    If group_values is None, returns an array filled with "all".
    This function is intentionally agnostic to clinical semantics.
    """
    if group_values is None:
        return np.asarray(["all"], dtype=object)
    return group_values.astype(object, copy=False)


def compute_active_mask(
    mass_source: np.ndarray,
    mass_target: np.ndarray,
    n_min_proto: float,
    eta_floor: float = 1e-12,
) -> tuple[np.ndarray, float]:
    """
    Pure mathematical semantic pruning:
        active_mask = (mass_source + mass_target >= n_min_proto)

    Returns:
      - active_mask
      - mass_pruned_ratio = fraction of (mass_source+mass_target) discarded
    """
    if mass_source.shape != mass_target.shape:
        raise ValueError("mass_source and mass_target must have the same shape")

    total = float(np.sum(mass_source + mass_target))
    active_mask = (mass_source + mass_target) >= float(n_min_proto)

    kept = float(np.sum((mass_source + mass_target)[active_mask]))
    pruned_ratio = 1.0 - (kept / (total + eta_floor))

    # Numerical guard: clamp to [0,1]
    pruned_ratio = float(max(0.0, min(1.0, pruned_ratio)))
    return active_mask, pruned_ratio


def weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    """
    Weighted quantile for non-negative weights.

    q in [0, 1]. Returns the smallest value such that cumulative weight >= q * total.
    """
    if not (0.0 <= q <= 1.0):
        raise ValueError("q must be in [0, 1]")
    if values.size == 0:
        raise ValueError("values must be non-empty")
    if weights.shape != values.shape:
        raise ValueError("weights must have the same shape as values")

    w_sum = float(np.sum(weights))
    if w_sum <= 0:
        # Degenerate: fall back to unweighted quantile
        return float(np.quantile(values, q))

    order = np.argsort(values)
    v = values[order]
    w = weights[order]
    cum = np.cumsum(w)
    threshold = q * w_sum
    idx = int(np.searchsorted(cum, threshold, side="left"))
    idx = min(max(idx, 0), v.size - 1)
    return float(v[idx])
