# Data Contracts

## 1. Input AnnData Object (`adata`)
The primary data structure is an `AnnData` object encompassing all cells across all patients, timepoints, and ROIs.

### 1.1 `adata.obs` (Cell Metadata)
Must contain the following columns (no missing values allowed for structural keys):
- `patient_id` (str): Unique identifier for the patient.
- `timepoint` (category/int): strictly `0` (pre) or `1` (post).
- `roi_id` (str): Unique identifier for the ROI.
- `compartment` (str, optional): User-provided spatial label (e.g., 'CT', 'PT', 'RTB').
- `cell_type` (str): Coarse identity (e.g., 'tumor', 'immune', 'stroma') derived from prior gating/clustering.
- `proto_id` (int, generated): Global prototype assignment $a(c) \in [1, K]$.
- `block_id` (str, generated): For single-ROI bootstrap adaptive grid mapping.

### 1.2 `adata.X` (Expression)
- Contains normalized (e.g., arcsinh transformed) marker expression matrix. Shape: `(n_cells, n_markers)`.

### 1.3 `adata.obsm` (Multidimensional Annotations)
- `spatial` (float array): Physical coordinates $(x, y)$. Shape: `(n_cells, 2)`.
- `community_features` (float array): The robustly scaled vector $\tilde{u}_c = [\mathbf{p}_c, \bar{\mathbf{m}}_c, \mathbf{m}_c, \delta_c]$. Shape: `(n_cells, d_u)`.

### 1.4 `adata.uns` (Unstructured Metadata)
- `roi_areas` (dict): Mapping of `roi_id` -> valid tissue area in $mm^2$.
- `global_cost_scale` (float): The median pairwise distance $s_C$.
- `lambda_dens` (dict): Calibrated $\lambda$ for density per group.
- `lambda_shape` (dict): Calibrated $\lambda$ for shape per group.
- `prototype_centers` (float array): Coordinates of $\mathbf{z}_k$. Shape: `(K, d_u)`.

## 2. Output Artifact Contracts
Output files must be generated via `src/avcp_template/io/bridge.py::save_for_r()` to enforce meta sidecars.

### 2.1 Metrics Table (`metrics_<level>.csv`)
Primary Key: `patient_group_id` (e.g., "P01_CT")
Columns: `patient_id`, `group_id`, `scale_ratio`, `T`, `D`, `B`, `M`, `R`, `tau`.
Must have `_meta.json` describing provenance.

### 2.2 Events Table (`events_<level>.parquet`)
Primary Key: `event_id` (e.g., "P01_CT_rem_5_12")
Columns: `patient_id`, `group_id`, `source_proto`, `target_proto`, `mass`, `cost`, `event_type` ('retention', 'remodeling', 'creation', 'destruction'), `drift_aligned` (bool), `reproducibility` (float).
