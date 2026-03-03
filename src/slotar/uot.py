from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .exceptions import (
    ERR_UOT_EMPTY_MASS_SOURCE,
    ERR_UOT_EMPTY_MASS_TARGET,
    ERR_UOT_EMPTY_SUPPORT,
    UOTInputError,
)
from .utils import compute_active_mask, weighted_quantile


@dataclass(frozen=True)
class UOTSolveConfig:
    """
    Numerical configuration for UOT solve.

    eps_schedule: e.g., [10.0, 5.0, 2.5, 1.0, 0.5, 0.2, 0.1]
    """
    eps_schedule: List[float]
    max_iter: int = 2000
    tol: float = 1e-6
    eta_floor: float = 1e-12
    n_min_proto: float = 0.0
    tau_q: float = 0.25
    tau_mode: str = "pi_weighted_q25"


def _get_pot_unbalanced_solver() -> Any:
    """
    POT compatibility shim: choose an available unbalanced Sinkhorn implementation.
    """
    import ot  # type: ignore

    if hasattr(ot, "unbalanced") and hasattr(ot.unbalanced, "sinkhorn_stabilized_unbalanced"):
        return ot.unbalanced.sinkhorn_stabilized_unbalanced
    if hasattr(ot, "unbalanced") and hasattr(ot.unbalanced, "sinkhorn_knopp_unbalanced"):
        return ot.unbalanced.sinkhorn_knopp_unbalanced
    raise ImportError("POT unbalanced Sinkhorn solver not found (expected ot.unbalanced.*)")


def solve_uot(
    a: np.ndarray,
    b: np.ndarray,
    C: np.ndarray,
    lam: float,
    cfg: UOTSolveConfig,
) -> Tuple[np.ndarray, Dict[str, float]]:
    """
    Solve entropic unbalanced OT with KL relaxation using POT.

    Plan B (Fail-fast):
      - If a.sum() == 0 or b.sum() == 0 -> raise UOTInputError
      - If active support after pruning is empty -> raise UOTInputError

    Notes:
      - alpha is NOT a solver parameter; calibration happens upstream.
      - This function is domain-agnostic (source/target, not pre/post).
    """
    a = np.asarray(a, dtype=float).reshape(-1)
    b = np.asarray(b, dtype=float).reshape(-1)
    C = np.asarray(C, dtype=float)

    if a.size == 0 or b.size == 0:
        raise UOTInputError(ERR_UOT_EMPTY_SUPPORT, "Empty a or b vector")
    if C.ndim != 2 or C.shape[0] != C.shape[1]:
        raise ValueError("C must be a square 2D cost matrix")
    if C.shape[0] != a.size or C.shape[1] != b.size:
        raise ValueError("C shape must match a and b length")

    sum_a = float(np.sum(a))
    sum_b = float(np.sum(b))
    if not np.isfinite(sum_a) or not np.isfinite(sum_b):
        raise ValueError("a/b sums must be finite")
    if sum_a <= 0:
        raise UOTInputError(ERR_UOT_EMPTY_MASS_SOURCE, f"sum_a={sum_a}")
    if sum_b <= 0:
        raise UOTInputError(ERR_UOT_EMPTY_MASS_TARGET, f"sum_b={sum_b}")
    if np.any(a < 0) or np.any(b < 0):
        raise ValueError("a and b must be non-negative")
    if not np.isfinite(C).all():
        raise ValueError("C must be finite")

    # Semantic pruning (active set)
    active_mask, mass_pruned_ratio = compute_active_mask(
        mass_source=a, mass_target=b, n_min_proto=cfg.n_min_proto, eta_floor=cfg.eta_floor
    )
    active_idx = np.where(active_mask)[0]
    if active_idx.size == 0:
        raise UOTInputError(
            ERR_UOT_EMPTY_SUPPORT,
            f"active_K=0 after pruning (mass_pruned_ratio={mass_pruned_ratio:.6f})",
        )

    aA = a[active_idx]
    bA = b[active_idx]
    CA = C[np.ix_(active_idx, active_idx)]

    if float(np.sum(aA)) <= 0:
        raise UOTInputError(ERR_UOT_EMPTY_MASS_SOURCE, "sum_a_active<=0 after pruning")
    if float(np.sum(bA)) <= 0:
        raise UOTInputError(ERR_UOT_EMPTY_MASS_TARGET, "sum_b_active<=0 after pruning")

    pot_solver = _get_pot_unbalanced_solver()

    PiA: Optional[np.ndarray] = None
    for eps in cfg.eps_schedule:
        if eps <= 0:
            raise ValueError("All eps in eps_schedule must be > 0")
        # POT: reg = eps (entropic regularization), reg_m = lam (mass relaxation)
        PiA = pot_solver(
            aA,
            bA,
            CA,
            reg=float(eps),
            reg_m=float(lam),
            numItermax=int(cfg.max_iter),
            stopThr=float(cfg.tol),
        )

        if not np.isfinite(PiA).all():
            raise RuntimeError(f"UOT produced non-finite Pi at eps={eps}")

    assert PiA is not None

    # Expand to full size for consistent downstream indexing
    K = a.size
    Pi = np.zeros((K, K), dtype=float)
    Pi[np.ix_(active_idx, active_idx)] = PiA

    # Metrics (computed on active subproblem)
    T = float(np.sum(PiA))
    pre_marg = np.sum(PiA, axis=1)
    post_marg = np.sum(PiA, axis=0)

    D_pos = float(np.sum(np.maximum(aA - pre_marg, 0.0)))
    B_pos = float(np.sum(np.maximum(bA - post_marg, 0.0)))
    d_rel = D_pos / (float(np.sum(aA)) + cfg.eta_floor)
    b_rel = B_pos / (float(np.sum(bA)) + cfg.eta_floor)

    M = float(np.sum(CA * PiA) / (T + cfg.eta_floor))

    # Retention labeling threshold tau (pi-weighted quantile of costs)
    tau = weighted_quantile(values=CA.reshape(-1), weights=PiA.reshape(-1), q=cfg.tau_q)
    R = float(np.sum(PiA[CA <= tau]) / (T + cfg.eta_floor))

    metrics: Dict[str, float] = {
        "T": T,
        "D_pos": D_pos,
        "B_pos": B_pos,
        "d_rel": float(d_rel),
        "b_rel": float(b_rel),
        "M": M,
        "R": R,
        "tau": float(tau),
        "mass_pruned_ratio": float(mass_pruned_ratio),
        "active_K": float(active_idx.size),
    }
    return Pi, metrics


def calibrate_lambdas(*args: Any, **kwargs: Any) -> Any:
    """
    Placeholder for calibration logic.

    This must be implemented in tasks/ pipelines (benchmark-specific orchestration),
    or as a library helper if it stays purely mathematical and contract-compliant.
    """
    raise NotImplementedError("calibrate_lambdas is not implemented yet (use tasks/* calibration).")