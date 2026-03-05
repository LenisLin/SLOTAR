"""
Module: src.slotar.utils
Architecture: Library Level
Constraints:
- Pure utility functions with strict isolation between semantic logic and numerical guards.
"""
from __future__ import annotations

import numpy as np

def compute_active_mask(
    mass_source: np.ndarray, 
    mass_target: np.ndarray, 
    n_min_proto: float,
    eta_floor: float = 1e-12
) -> tuple[np.ndarray, float]:
    """
    Computes the mathematical active support mask for optimal transport, decoupling
    semantic pruning from numerical stabilization.

    Args:
        mass_source: 1D array of shape [K].
        mass_target: 1D array of shape [K].
        n_min_proto: Semantic threshold for active support inclusion.
        eta_floor: Numerical guard constant (used only for zero-division prevention, NOT masking).

    Returns:
        active_mask: 1D boolean array of shape [K]. True if (source + target >= n_min_proto).
        mass_pruned_ratio: Float indicating the ratio of mass lost due to semantic pruning.

    Constraints for Codex:
        1. The mask MUST purely evaluate `mass_source + mass_target >= n_min_proto`.
        2. `mass_pruned_ratio` MUST be calculated on the original mass sum before any 
           `eta_floor` padding is applied.
        3. Do NOT add `eta_floor` to the returned mask or manipulate the mass tensors here.
    """
    raise NotImplementedError(
        "Codex: Implement the pure mathematical active mask and mass pruned ratio logic here."
    )

def weighted_quantile(
    values: np.ndarray, 
    weights: np.ndarray, 
    q: float
) -> float:
    """
    Computes a weighted quantile, used for setting the retention threshold (tau).
    
    Args:
        values: 1D array of shape [N] containing the data points (e.g., costs).
        weights: 1D array of shape [N] containing the weights (e.g., Pi matrix elements).
        q: Quantile to compute (0.0 <= q <= 1.0).
        
    Returns:
        The interpolated weighted quantile value.
    """
    raise NotImplementedError(
        "Codex: Implement standard weighted quantile logic. Handle cases where sum(weights) == 0."
    )