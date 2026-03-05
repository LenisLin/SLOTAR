"""
Module: src.slotar.representation
Architecture: Library Level (Prerequisite Inputs)
Constraints:
- STRICTLY NO references to `tasks`, `config.yaml`, or clinical metadata.
- These are upstream utilities. They must mutate the AnnData object in-place to comply 
  with SLOTAR data contracts.
"""
from __future__ import annotations

from typing import Any

import numpy as np

try:
    from anndata import AnnData
except ImportError:  # pragma: no cover
    AnnData = Any  # type: ignore[misc,assignment]


def build_community_features(adata: AnnData, k: int = 30) -> None:
    """
    Computes spatial community features based on exact kNN and local density.

    Args:
        adata: AnnData object containing `.obsm['spatial']`.
        k: Number of nearest neighbors.

    Side Effects:
        - Stores robustly scaled vectors in `adata.obsm['community_features']`.
        - Stores scaling parameters in `adata.uns['scaler_params']`.

    Constraints for Codex:
        1. FAIL-FAST: Raise ValueError if NaNs are found in `adata.obsm['spatial']`.
        2. DENSITY & EXACT KNN: You MUST calculate the local density delta_c = k / (pi * r_k^2) 
           using exact kNN distances, and include it in the feature matrix before scaling.
        3. SCALER PARAMS: You MUST compute robust scaling (e.g., median/IQR) and save the 
           parameters to `adata.uns['scaler_params']` for auditability.
    """
    raise NotImplementedError(
        "Codex: Implement exact kNN, density calculation, robust scaling, and save scaler_params."
    )


def learn_global_prototypes(adata: AnnData, n_bal: int, K: int, random_state: int = 42) -> None:
    """
    Learns global prototypes via balanced sub-sampling and KMeans clustering.

    Args:
        adata: AnnData object containing `.obsm['community_features']`.
        n_bal: Number of cells to sample per ROI/category for balanced clustering.
        K: Number of prototypes (clusters) to discover.
        random_state: Seed for reproducibility.

    Side Effects:
        - Assigns cluster IDs to `adata.obs['proto_id']`.
        - Computes the global cost scale and stores it in `adata.uns['s_C']`.
        - Stores the KMeans centroids in `adata.uns['prototype_centroids']`.

    Constraints for Codex:
        1. DETERMINISM: You MUST use the `random_state` for both subsampling and KMeans.
        2. AUDIT TRAIL: Save the learned cluster centers to `adata.uns['prototype_centroids']`.
        3. CANONICAL NAMES: You MUST write the cost scale exactly to `adata.uns['s_C']`.
    """
    raise NotImplementedError(
        "Codex: Implement balanced sampling, deterministic KMeans, save centroids, and compute s_C."
    )
