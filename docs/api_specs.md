# API Specifications

## Module 1: Representation (`slotar.representation`)

### `build_community_features(adata: AnnData, k: int = 30) -> None`
- **Inputs**: `adata` with `.obsm['spatial']` and `.obs['cell_type']`.
- **Side Effects**: Computes $\tilde{u}_c$ and stores it in `adata.obsm['community_features']`. Fails fast if coordinates contain NaNs.
- **Constraints**: Uses exact kNN. Computes density $\delta_c = k / (\pi \cdot r_k^2)$.

### `learn_global_prototypes(adata: AnnData, n_bal: int, K: int) -> None`
- **Side Effects**: Computes balanced sample $\mathcal{U}_{bal}$, runs KMeans, assigns `proto_id` to all cells in `adata.obs`. Computes and stores $s_C$ in `adata.uns['global_cost_scale']`.

## Module 2: UOT Engine & Calibration (`slotar.uot`)

### `calibrate_lambdas(adata: AnnData, target_alpha: float = 0.05) -> Tuple[Dict, Dict]`
- **Inputs**: Annotated `adata` with prototype counts per ROI.
- **Outputs**: Returns two dictionaries `{group: lambda}` for density and shape levels.
- **Constraints**: Uses only `timepoint == 0` ROIs.

### `solve_uot(a: np.ndarray, b: np.ndarray, C: np.ndarray, lam: float, eps_init: float = 10.0, eps_target: float = 0.1) -> Tuple[np.ndarray, dict]`
- **Inputs**: Non-negative mass vectors `a`, `b`, scaled cost matrix `C`.
- **Outputs**: Coupling matrix $\Pi^*$ and metrics dict (T, B, D, M, R).
- **Constraints**: Must enforce $\varepsilon$-scaling and log-domain computation. Inputs $a, b$ are pruned for support $> \eta$.

## Module 3: Uncertainty Quantification (`slotar.uq`)

### `bootstrap_single_roi(adata: AnnData, roi_id: str, G: int, B_boot: int) -> dict`
- **Inputs**: Subset of `adata` corresponding to a single ROI.
- **Outputs**: Dictionary of confidence intervals and event frequencies.
- **Constraints**: Cannot recompute kNN or prototypes. Only samples cell indices based on adaptive $G \times G$ blocks. Drops blocks with `< n_min` cells.
