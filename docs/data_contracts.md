# Data Contracts (SLOTAR V1.6)

## 1. Input AnnData Object (`adata`)
The primary data structure is an `AnnData` object encompassing all cells.

### 1.1 `adata.obs` (Cell Metadata)
- `patient_id` (str), `timepoint` (int: 0/1), `roi_id` (str), `compartment` (str).
- `cell_type` (str): Coarse identity (e_c).
- `proto_id` (int, generated): Global prototype assignment $a(c)$.
- `block_id` (str, generated): For frozen-feature block bootstrap.

### 1.2 `adata.obsm` & `adata.uns`
- `.obsm['spatial']`: Coordinates $(x, y)$.
- `.obsm['community_features']`: Robustly scaled vector $\tilde{u}_c$.
- `.uns['scaler_params']`: Median/MAD parameters used for $\tilde{u}_c$ (Required for drift alignment).
- `.uns['roi_areas']`: Mapping of `roi_id` -> effective area in $mm^2$.
- `.uns['s_C']`: Global static cost scale.

## 2. Output Artifact Contracts
Generated via `src/avcp_template/io/bridge.py::save_for_r()`.

### 2.1 Metrics Table (`metrics_<level>.csv`)
Primary Key: `patient_group_id`
Core Metrics: `S0`, `S1`, `scale_ratio`, `T`, `D_pos`, `B_pos`, `d_rel`, `b_rel`, `M`, `R`, `tau`.
Audit Fields: `A_pre`, `A_post`, `area_mode`, `mass_pruned_ratio`, `tau_mode`.
**Bypass Contract**: 
- If `uot_status != "ok"`:
  - All UOT metrics (`T`, `D_pos`, `B_pos`, `d_rel`, `b_rel`, `M`, `R`, `tau`) MUST be written as explicit `NaN` (which translates to `NA` in R).
  - The corresponding `events` table partition MUST be empty.
  - If bypassed due to `empty_support_after_prune`, `mass_pruned_ratio` must be set to `1.0`.

### 2.2 Events Table (`events_<level>.parquet`)
Primary Key: `event_id`
Columns: `source_proto`, `target_proto`, `mass`, `cost`, `event_type` ('retention', 'remodeling', 'creation', 'destruction'), `drift_aligned` (bool), `reproducibility` (float).

# Data Contracts

## SLOTAR V1.6 Output Specifications

### 1. Global Audit Fields (Mandatory for reproducibility)
- `lambda_dens`: dict, keys are groups $g$, values are float.
- `lambda_shape`: dict, keys are groups $g$, values are float.
- `tau_g`: dict, keys are groups $g$, values are float (baseline calibrated threshold).
- `s_C`: float, global static cost scaling factor.
- `eta_floor`: float, numerical floor for log-domain stability (e.g., 1e-12).
- `n_min_proto`: int, semantic active set minimum count threshold.
- `mass_pruned_ratio`: float, ratio of mass dropped during active set pruning. Triggers warning if > 0.5%.
- `UQ_mode`: string, enum `["roi_bootstrap", "grid_block_frozen", "moving_block_optional"]`.
- `area_mode`: string, enum `["mask", "nominal"]`.
- `eps_schedule_id`: string or list, the exact annealing schedule used for Sinkhorn.
- `delta_mode`: string, defines density term adaptation (e.g., `"const"`, `"spot_density"`).
- `p_mode`: string, defines composition term adaptation (e.g., `"zero"`, `"soft_comp"`).
- `slide_match`: string, enum `["yes", "no", "unknown"]`, mandatory for cross-organ ST pairs.
- `drift_mode`: string, enum `["standard", "unavailable"]`, dictates if drift vector can be reliably estimated.
- `uot_status`: string, enum `["ok", "bypassed_structural_zero", "bypassed_empty_support", "error"]`. Tracks solver bypass status.
- `bypass_reason`: string, enum `["S0_zero", "S1_zero", "empty_support_after_prune", null]`.

### 2. Patient-Group Output Object $(p, g)$
- **Scale**:
  - `S0`, `S1`: float, total cells / total mm² for pre and post.
  - `scale_ratio`: float, $S1 / S0$.
  - `audit_pre`, `audit_post`: dict, containing `A` (effective area), `n_roi`, `n_cells`.
- **Density-level & Shape-level UOT**:
  - `metrics`: dict containing `T`, `D_pos`, `B_pos`, `d_rel`, `b_rel`, `M`, `R`, `tau`.
  - `events`: Event extraction table tracking retention/remodeling/creation/destruction.
- **Batch Drift Risk**:
  - `drift_aligned`: boolean flag attached to remodeling edges if cosine similarity with batch drift vector > 0.85 (computed in equivalent scaled subspace).
