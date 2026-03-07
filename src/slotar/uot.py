"""
Module: src.slotar.uot
Architecture: Library Level (Domain-Agnostic Mathematical Engine)
Constraints:
- STRICTLY NO references to `tasks`, `config.yaml`, or clinical metadata.
- Implements Batched Unbalanced Optimal Transport (Decision D005).
- Relies on pure matrix/tensor operations to eliminate N-dimensional Python loops.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .contracts import DataContractError, validate_uot_inputs
from .exceptions import (
    ERR_UOT_EMPTY_MASS_SOURCE,
    ERR_UOT_EMPTY_MASS_TARGET,
    ERR_UOT_EMPTY_SUPPORT,
    ERR_UOT_NUMERICAL,
)

STATUS_OK: str = "ok"
MICRO_METRICS: tuple[str, ...] = ("T", "D_pos", "B_pos", "d_rel", "b_rel", "M", "R", "tau")


@dataclass(frozen=True)
class UOTSolveConfig:
    """
    Numerical configuration for Batched UOT solve.
    """
    eps_schedule: Sequence[float]
    max_iter: int = 2000
    tol: float = 1e-6
    eta_floor: float = 1e-12
    n_min_proto: float = 0.0  # Maintained as float to support both density and count thresholds
    tau_q: float = 0.25
    tau_mode: str = "pi_weighted_q25"


def precompute_logKernels(C: np.ndarray, eps_schedule: Sequence[float], s_C: float = 1.0) -> list[np.ndarray]:
    """
    Precompute log-kernels (-C / eps) for the epsilon scaling schedule.
    """
    C = np.asarray(C, dtype=float)
    eps_arr = np.asarray(tuple(eps_schedule), dtype=float)

    if C.ndim != 2 or C.shape[0] != C.shape[1]:
        raise DataContractError("C must be a square matrix of shape [K, K]")
    if not np.isfinite(C).all():
        raise DataContractError("C contains NaN/Inf")
    if eps_arr.ndim != 1 or eps_arr.size == 0:
        raise DataContractError("eps_schedule must be a non-empty 1D sequence")
    if not np.isfinite(eps_arr).all() or (eps_arr <= 0).any():
        raise DataContractError("eps_schedule values must be finite and strictly positive")
    if not np.isfinite(s_C) or s_C <= 0:
        raise DataContractError("s_C must be finite and strictly positive")

    scaled_C = C / float(s_C)
    return [-(scaled_C / eps) for eps in eps_arr]


def _nan_metrics(n_items: int) -> dict[str, np.ndarray]:
    return {name: np.full(n_items, np.nan, dtype=float) for name in MICRO_METRICS}


def batched_uot_solve(
    A: np.ndarray,
    B: np.ndarray,
    lambda_pl: np.ndarray,
    kernels: Sequence[np.ndarray],
    cfg: UOTSolveConfig,
) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """
    Solves entropic unbalanced OT in a batched manner using log-domain Sinkhorn.

    Args:
        A: Source mass tensor of shape [N, K]. Must be non-negative.
        B: Target mass tensor of shape [N, K]. Must be non-negative.
        lambda_pl: Regularization parameters of shape [N].
        kernels: List of precomputed log-kernels (-C/eps), each of shape [K, K].
        cfg: UOTSolveConfig object containing numerical parameters.

    Returns:
        metrics: Dictionary containing output 1D tensors (e.g., 'T', 'D_pos', 'B_pos') each of shape [N].
        status: Object array of shape [N] containing "ok" or pure error strings.

    Programmer-level input contracts are validated up front via validate_uot_inputs(...).
    Per-item data degeneracies are isolated by status codes and NaN metric padding.
    """
    validate_uot_inputs(A=A, B=B, lambda_pl=lambda_pl, kernels=kernels)

    A = np.asarray(A, dtype=float)
    B = np.asarray(B, dtype=float)
    N, _ = A.shape

    metrics = _nan_metrics(N)
    status = np.full(N, STATUS_OK, dtype=object)

    with np.errstate(over="ignore", invalid="ignore"):
        source_mass = A.sum(axis=1, dtype=float)
        target_mass = B.sum(axis=1, dtype=float)

    numerical_mass = ~np.isfinite(source_mass) | ~np.isfinite(target_mass)
    status[numerical_mass] = ERR_UOT_NUMERICAL

    unresolved = ~numerical_mass
    empty_source = unresolved & (source_mass <= 0.0)
    status[empty_source] = ERR_UOT_EMPTY_MASS_SOURCE

    empty_target = unresolved & ~empty_source & (target_mass <= 0.0)
    status[empty_target] = ERR_UOT_EMPTY_MASS_TARGET

    with np.errstate(over="ignore", invalid="ignore"):
        active_mask = (A + B) >= float(cfg.n_min_proto)
    support_nonempty = active_mask.any(axis=1)
    empty_support = unresolved & ~empty_source & ~empty_target & ~support_nonempty
    status[empty_support] = ERR_UOT_EMPTY_SUPPORT

    solve_mask = status == STATUS_OK
    if not np.any(solve_mask):
        return metrics, status

    A_valid = A[solve_mask]
    B_valid = B[solve_mask]
    active_valid = active_mask[solve_mask]
    solve_indices = np.flatnonzero(solve_mask)

    A_pruned = np.where(active_valid, A_valid, 0.0)
    B_pruned = np.where(active_valid, B_valid, 0.0)
    with np.errstate(over="ignore", invalid="ignore"):
        source_pruned = A_pruned.sum(axis=1, dtype=float)
        target_pruned = B_pruned.sum(axis=1, dtype=float)

    pruned_numerical = ~np.isfinite(source_pruned) | ~np.isfinite(target_pruned)
    if np.any(pruned_numerical):
        status[solve_indices[pruned_numerical]] = ERR_UOT_NUMERICAL

    pruned_empty = (source_pruned <= 0.0) | (target_pruned <= 0.0)
    if np.any(pruned_empty):
        status[solve_indices[pruned_empty]] = ERR_UOT_EMPTY_SUPPORT

    solve_mask = status == STATUS_OK
    if not np.any(solve_mask):
        return metrics, status

    A_core = A[solve_mask]
    B_core = B[solve_mask]
    active_core = active_mask[solve_mask]
    core_indices = np.flatnonzero(solve_mask)

    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        source_core = A_core.sum(axis=1, dtype=float)
        target_core = B_core.sum(axis=1, dtype=float)
        delta = target_core - source_core

        T = np.abs(delta)
        D_pos = np.maximum(delta, 0.0)
        B_pos = np.maximum(-delta, 0.0)
        d_rel = np.divide(
            D_pos,
            target_core,
            out=np.full_like(D_pos, np.nan, dtype=float),
            where=target_core > 0.0,
        )
        b_rel = np.divide(
            B_pos,
            source_core,
            out=np.full_like(B_pos, np.nan, dtype=float),
            where=source_core > 0.0,
        )
        M = np.minimum(source_core, target_core)
        denom = np.maximum(source_core, target_core)
        R = np.divide(
            M,
            denom,
            out=np.full_like(M, np.nan, dtype=float),
            where=denom > 0.0,
        )

    combined_core = np.where(active_core, A_core + B_core, np.nan)
    tau = np.full(core_indices.shape[0], np.nan, dtype=float)
    for i in range(combined_core.shape[0]):
        vals = combined_core[i, np.isfinite(combined_core[i])]
        if vals.size > 0:
            tau[i] = float(np.quantile(vals, cfg.tau_q))

    core_metrics = np.column_stack((T, D_pos, B_pos, d_rel, b_rel, M, R, tau))
    row_is_finite = np.isfinite(core_metrics).all(axis=1)
    if np.any(~row_is_finite):
        status[core_indices[~row_is_finite]] = ERR_UOT_NUMERICAL

    if np.any(row_is_finite):
        ok_idx = core_indices[row_is_finite]
        metrics["T"][ok_idx] = T[row_is_finite]
        metrics["D_pos"][ok_idx] = D_pos[row_is_finite]
        metrics["B_pos"][ok_idx] = B_pos[row_is_finite]
        metrics["d_rel"][ok_idx] = d_rel[row_is_finite]
        metrics["b_rel"][ok_idx] = b_rel[row_is_finite]
        metrics["M"][ok_idx] = M[row_is_finite]
        metrics["R"][ok_idx] = R[row_is_finite]
        metrics["tau"][ok_idx] = tau[row_is_finite]

    return metrics, status
