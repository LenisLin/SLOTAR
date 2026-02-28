# Overall Validation Plan (Evidence Chain)

## 1. Benchmark A: Single-timepoint Controlled Stress Test
- **Data**: Public Single-timepoint IMC (35 markers, ~9 ROIs/patient).
- **Purpose**: Validate selection-awareness (unmatched mass absorbs bias), UQ calibration (CI width vs coverage), and synthetic drift flagging under a strict zero-effect counterfactual constraint.

## 2. Benchmark B: Public Longitudinal Spatial Proteomics
- **Data**: TONIC TNBC spatiotemporal dataset.
- **Purpose**: Demonstrate operational longitudinal decomposition (baseline -> on-treatment), cohort-level structural zero inference, and robustness of single-ROI UQ within a real-world clinical context.

## 3. Benchmark C & C': Private Clinical Cohort (Ultimate Application)
- **Data**: Main multi-ROI Gastric Cancer IMC (pCR vs NR) + External site replication.
- **Purpose**: Provide mechanism-level attribution (RTB/AB remapping) and demonstrate the tool's indispensability in handling severe asymmetric sampling and compartmental structural zeros.

## 4. Optional Vignette: Cross-modality Generalization
- **Data**: Public PDAC Spatial Transcriptomics (Primary -> Metastasis).
- **Purpose**: Prove the mathematical abstraction of "measure alignment" is independent of protein panels and treatment interventions.
