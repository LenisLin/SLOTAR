from __future__ import annotations

import numpy as np
import pandas as pd


def flag_drift(
    events: pd.DataFrame,
    z: np.ndarray,
    drift_vector: np.ndarray | None = None,
    thr: float = 0.85,
) -> tuple[pd.DataFrame, str]:
    """
    Drift risk flagging (consumer-only).
    - If drift_vector is None: drift_mode="unavailable" and drift_aligned set to NA.
    - Else: compute cosine alignment between (z_j - z_i) and drift_vector.

    Expected events columns: ['source_proto','target_proto','event_type'].
    Only rows with event_type == 'remodeling' are flagged; others get False/NA.
    """
    out = events.copy()

    if "drift_aligned" not in out.columns:
        out["drift_aligned"] = pd.NA

    if drift_vector is None:
        out["drift_aligned"] = pd.NA
        return out, "unavailable"

    dv = np.asarray(drift_vector, dtype=float).reshape(-1)
    if not np.isfinite(dv).all() or float(np.linalg.norm(dv)) == 0.0:
        out["drift_aligned"] = pd.NA
        return out, "unavailable"

    def _cos(u: np.ndarray, v: np.ndarray) -> float:
        nu = float(np.linalg.norm(u))
        nv = float(np.linalg.norm(v))
        if nu == 0.0 or nv == 0.0:
            return 0.0
        return float(np.dot(u, v) / (nu * nv))

    aligned = []
    for _, row in out.iterrows():
        if row.get("event_type") != "remodeling":
            aligned.append(False)
            continue
        i = int(row["source_proto"])
        j = int(row["target_proto"])
        vec = np.asarray(z[j] - z[i], dtype=float).reshape(-1)
        score = _cos(vec, dv)
        aligned.append(bool(score > thr))

    out["drift_aligned"] = aligned
    return out, "provided"
