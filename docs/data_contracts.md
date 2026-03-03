# Data Contracts (SLOTAR V1.6)

## 1. Input AnnData Object (`adata`)
The primary data structure is an `AnnData` object encompassing all cells/spots.

### 1.1 `adata.obs` (Observation Metadata)
- `patient_id` (str), `timepoint` (int: 0/1), `roi_id` (str), `compartment` (str).
- `cell_type` (str): Coarse identity (e_c) (optional depending on modality).
- `proto_id` (int, generated): Global prototype assignment a(c).
- `block_id` (str, generated): For frozen-feature block bootstrap (single ROI).

### 1.2 `adata.obsm` & `adata.uns`
- `.obsm['spatial']`: Coordinates (x, y).
- `.obsm['community_features']`: Robustly scaled vector u_tilde.
- `.uns['scaler_params']`: Robust scaling params (required for drift alignment audits).
- `.uns['roi_areas']`: Mapping roi_id -> effective area in mm^2.
- `.uns['s_C']`: Global static cost scale.

## 2. Output Artifact Contracts
Generated via `src/slotar/io/bridge.py::save_for_r()` (Python -> R handoff).

### 2.1 Metrics Table (`metrics_.csv`)
Primary Key: `patient_group_id`

Core Metrics:
- `S0`, `S1`, `scale_ratio`
- `T`, `D_pos`, `B_pos`, `d_rel`, `b_rel`, `M`, `R`, `tau`

Audit Fields:
- `A_pre`, `A_post`, `area_mode`, `mass_pruned_ratio`, `tau_mode`
- `uot_status`, `bypass_reason`
- `drift_mode`, `slide_match`
- `UQ_mode`, `n_blocks_valid`

**Bypass Contract (Plan B)**:
- If `uot_status != "ok"`:
  - All UOT metrics (`T`, `D_pos`, `B_pos`, `d_rel`, `b_rel`, `M`, `R`, `tau`) MUST be explicit `NaN` (-> `NA` in R).
  - The corresponding `events` partition MUST be empty.
- If bypassed due to `empty_support_after_prune`, `mass_pruned_ratio` must be set to `1.0`.

### 2.2 Events Table (`events_.parquet`)
Primary Key: `event_id`

Columns:
- `source_proto`, `target_proto`, `mass`, `cost`,
- `event_type` ∈ {'retention','remodeling','creation','destruction'},
- `drift_aligned` (bool or NA),
- `reproducibility` (float)

## 3. Global Audit Fields (Mandatory)
- `lambda_dens`, `lambda_shape`, `tau_g`, `s_C`, `eta_floor`, `n_min_proto`
- `mass_pruned_ratio`, `eps_schedule_id`
- `delta_mode`, `p_mode`
- `group_mode` ∈ {"all", "provided", "roi_state_cluster"} (implicit clustering forbidden)
- `drift_mode` ∈ {"provided", "unavailable"}
- `uot_status` ∈ {"ok","bypassed_structural_zero","bypassed_empty_support","error"}
- `bypass_reason` ∈ {"S0_zero","S1_zero","empty_support_after_prune", null}