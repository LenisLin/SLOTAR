from __future__ import annotations

import numpy as np

# Adjust the import path if your compute_log_measurement_error is located elsewhere
from slotar.uq import compute_log_measurement_error 


def test_compute_log_measurement_error_homogeneous_bound() -> None:
    """
    Test that highly homogeneous bootstrap replicates (near-zero variance)
    trigger the numerical lower bound (s2_lower_bound) to prevent weight explosion.
    """
    theta_replicates = np.full(100, 2.5)  # Identical estimates, variance = 0
    s2_log, bound_applied = compute_log_measurement_error(
        theta_replicates, 
        delta_stabilizer=1e-4, 
        s2_lower_bound=1e-6
    )
    
    assert s2_log == 1e-6
    assert bound_applied is True


def test_compute_log_measurement_error_with_structural_zeros() -> None:
    """
    Test that the delta stabilizer successfully handles zero-valued estimates 
    without generating -inf or NaN.
    """
    theta_replicates = np.array([0.0, 0.0, 1.0, 2.0, 0.0])
    s2_log, bound_applied = compute_log_measurement_error(
        theta_replicates, 
        delta_stabilizer=1e-4, 
        s2_lower_bound=1e-6
    )
    
    assert s2_log > 1e-6
    assert bound_applied is False
    assert np.isfinite(s2_log)