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

### `solve_uot(a: np.ndarray, b: np.ndarray, C: np.ndarray, lam: float, eps_schedule: list, ...) -> Tuple[np.ndarray, dict]`
- **Inputs**: Non-negative mass vectors `a`, `b`, scaled cost matrix `C`. (Note: $\alpha$ is a calibration target tolerance and MUST NOT be passed to this solver).
- **Preconditions (Strict)**: 
  - `a.sum() > 0` and `b.sum() > 0`.
  - Active support size after semantic pruning must be $> 0$.
- **Raises (Fail-fast)**: 
  - Raises `ValueError` explicitly with codes `ERR_UOT_EMPTY_MASS_PRE`, `ERR_UOT_EMPTY_MASS_POST`, or `ERR_UOT_EMPTY_SUPPORT` if preconditions fail. The solver must NEVER silently return `NaN` or zero matrices on invalid inputs.
- **Outputs**: Coupling matrix $\Pi^*$ and metrics dict (T, B_pos, D_pos, d_rel, b_rel, M, R, tau).
- **Constraints**: Pipeline/Wrapper layer is responsible for intercepting structural zeros ($I_{p,t,g}=0$) prior to calling this function.

## Module 3: Uncertainty Quantification (`slotar.uq`)

### `bootstrap_single_roi(adata: AnnData, roi_id: str, G: int, B_boot: int) -> dict`
- **Inputs**: Subset of `adata` corresponding to a single ROI.
- **Outputs**: Dictionary of confidence intervals and event frequencies.
- **Constraints**: Cannot recompute kNN or prototypes. Only samples cell indices based on adaptive $G \times G$ blocks. Drops blocks with `< n_min` cells.

### ST Modality Adaptation (Visium)
- **Inputs**: ST embedding (e.g., PCA on HVGs).
- **Adaptation**: 
  - $\mathbf{m}_c$: PCA vector of the spot.
  - $\bar{\mathbf{m}}_c$: kNN mean PCA vector ($k=20$).
  - $\delta_c$: Treated as constant (`delta_mode="const"`).
  - $\mathbf{p}_c$: Zero vector (`p_mode="zero"`) by default.
- **Constraints**: Enforces physical mapping without unsupported biological proxy claims.