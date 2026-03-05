from __future__ import annotations

import numpy as np

from slotar.exceptions import (
    ERR_UOT_EMPTY_MASS_SOURCE,
    ERR_UOT_EMPTY_SUPPORT,
)
from slotar.uot import UOTSolveConfig, batched_uot_solve, precompute_logKernels


def test_batched_uot_solve_batch_isolation() -> None:
    """
    Test that the batched solver isolates bad items without crashing the entire batch.
    Item 0: Valid data.
    Item 1: Empty source mass (ERR_UOT_EMPTY_MASS_SOURCE).
    Item 2: Will fail pruning due to extremely low mass vs n_min_proto (ERR_UOT_EMPTY_SUPPORT).
    """
    N, K = 3, 2
    A = np.array([
        [1.0, 1.0],             # Item 0: OK
        [0.0, 0.0],             # Item 1: Empty mass
        [1e-13, 1e-13]          # Item 2: Empty support after pruning
    ])
    B = np.array([
        [1.0, 1.0],
        [1.0, 1.0],
        [1.0, 1.0]
    ])
    
    lam_pl = np.array([1.0, 1.0, 1.0])
    C = np.zeros((K, K))
    
    # Configure high n_min_proto to force Item 2 to drop its active support
    cfg = UOTSolveConfig(eps_schedule=[1.0], n_min_proto=1e-5)
    kernels = precompute_logKernels(C, cfg.eps_schedule)

    metrics, status = batched_uot_solve(A=A, B=B, lambda_pl=lam_pl, kernels=kernels, cfg=cfg)

    # Assert shape correctness
    assert status.shape == (N,)
    assert metrics["D_pos"].shape == (N,)

    # Assert strict state isolation
    assert status[0] == "ok"
    assert status[1] == ERR_UOT_EMPTY_MASS_SOURCE
    # NOTE: Assuming batched_uot_solve implements the active mask pruning correctly
    # and assigns ERR_UOT_EMPTY_SUPPORT to items failing the mask check.
    assert status[2] == ERR_UOT_EMPTY_SUPPORT

    # Assert bypassed items return NaN for metrics
    assert not np.isnan(metrics["D_pos"][0])
    assert np.isnan(metrics["D_pos"][1])
    assert np.isnan(metrics["D_pos"][2])