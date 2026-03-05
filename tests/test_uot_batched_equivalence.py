from __future__ import annotations

import numpy as np

from slotar.uot import UOTSolveConfig, batched_uot_solve, precompute_logKernels


def test_batched_uot_tensor_integrity() -> None:
    """
    Test that the batched solver processes valid [N, K] tensors successfully
    and populates the metric arrays properly without triggering fallbacks.
    """
    np.random.seed(42)
    N, K = 5, 4
    
    A = np.random.rand(N, K) + 0.1  # Ensure strictly positive mass
    B = np.random.rand(N, K) + 0.1
    lam_pl = np.ones(N) * 0.5
    C = np.random.rand(K, K)
    
    cfg = UOTSolveConfig(eps_schedule=[1.0, 0.1])
    kernels = precompute_logKernels(C, cfg.eps_schedule)

    metrics, status = batched_uot_solve(A=A, B=B, lambda_pl=lam_pl, kernels=kernels, cfg=cfg)

    assert status.shape == (N,)
    assert np.all(status == "ok")
    
    # Verify core output tensors
    expected_metrics = ["T", "D_pos", "B_pos", "d_rel", "b_rel", "M", "R", "tau"]
    for m in expected_metrics:
        assert m in metrics
        assert metrics[m].shape == (N,)
        assert np.all(np.isfinite(metrics[m]))