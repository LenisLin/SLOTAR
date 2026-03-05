# API Specifications

## Module 1: Representation (Prerequisite Inputs)
*Note: This module provides utilities to convert spatial omics data into probability masses. The specific feature engineering (kNN, prototypes) is treated as an upstream prerequisite, not the core mathematical contribution of SLOTAR.*

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

### `batched_uot_solve(A: np.ndarray, B: np.ndarray, lambda_pl: np.ndarray, kernels: list, solver_config: dict) -> Tuple[dict, np.ndarray]`
- **Inputs**: 
  - `A`, `B`: Non-negative mass tensors of shape `[N, K]` (where N is the batch dimension: patients, lambdas, or bootstrap replicates).
  - `lambda_pl`: Array of shape `[N]` containing the regularization parameter for each batch item.
  - `kernels`: Precomputed log-domain kernels for the $\varepsilon$-scaling schedule.
- **Preconditions (Strict)**: 
  - Handled via active masks. Structural zeros MUST be bypassed by the caller before entering the solver, OR the solver must return specific error codes in the status array without crashing the entire batch.
- **Outputs**: 
  - `metrics_dict`: Dictionary of batched tensors for `T`, `B_pos`, `D_pos`, `d_rel`, `b_rel`, `M`, `R`, `tau`.
  - `status_array`: Array of shape `[N]` with values `"ok"`, `"ERR_UOT_EMPTY_MASS"`, or `"ERR_UOT_EMPTY_SUPPORT"`.
- **Constraints**: 
  - Strictly no Python `for`-loops over the batch dimension $N$ during Sinkhorn iterations. Must use vectorized matrix operations and broadcasting.

## Module 3: Uncertainty Quantification (`slotar.uq`)

### `bootstrap_single_roi(adata: AnnData, roi_id: str, G: int, B_boot: int) -> dict`
- **Inputs**: Subset of `adata` corresponding to a single ROI.
- **Outputs**: Dictionary of bootstrap replicates and the log-scale empirical variance.
- **Constraints**: 
  - MUST enforce frozen representations (Cannot recompute kNN or prototypes).
  - MUST compute the empirical measurement error strictly as $s_i^2 := \text{Var}(\log(\hat{\theta}_i^{(b)} + \delta))$, ensuring numerical bounds are applied per V2.0 contracts.

### ST Modality Adaptation (Visium)
- **Inputs**: ST embedding (e.g., PCA on HVGs).
- **Adaptation**: 
  - $\mathbf{m}_c$: PCA vector of the spot.
  - $\bar{\mathbf{m}}_c$: kNN mean PCA vector ($k=20$).
  - $\delta_c$: Treated as constant (`delta_mode="const"`).
  - $\mathbf{p}_c$: Zero vector (`p_mode="zero"`) by default.
- **Constraints**: Enforces physical mapping without unsupported biological proxy claims.

## Module 4: Domain-Agnostic Utilities (`slotar.utils`)

### `build_grouping(adata, group_key: Optional[str] = None) -> np.ndarray`
- **Inputs**: `group_key` (column name in `adata.obs`).
- **Logic**: If `group_key` is None or not provided, MUST fallback to assigning all observations to a single group: `g="all"`. Implicit ROI-state clustering is strictly forbidden. 
- **Outputs**: Group assignments array.

### `compute_active_mask(mass_source: np.ndarray, mass_target: np.ndarray, n_min_proto: float) -> Tuple[np.ndarray, float]`
- **Inputs**: Source and target mass vectors (agnostic to temporal pre/post semantics).
- **Logic**: Mathematical pure mask `active_mask = (mass_source + mass_target >= n_min_proto)`. 
- **Outputs**: `active_mask` (boolean array) and `mass_pruned_ratio` (float).

### `flag_drift(events: dict, z: np.ndarray, drift_vector: Optional[np.ndarray] = None, thr: float = 0.85) -> dict`
- **Inputs**: `drift_vector` MUST be computed by the upstream task pipeline and passed explicitly. The library performs NO automatic drift estimation.
- **Logic**: If `drift_vector` is None, skips cosine computation.
- **Outputs**: Returns events with `drift_aligned` flags. If `drift_vector` is None, sets `drift_aligned = null` and signals unavailable mode.