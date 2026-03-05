# Benchmark B Specification (TONIC Validation)

## 1. Transition and Compartments
- **Transition Locked**: `baseline` $\to$ `on-treatment`.
- **Macro-Compartments ($g$)**: Hardcode foldings into `tumor`, `stroma`, `interface` to prevent structural zero inflation.

## 2. UQ and Single-ROI Strategy (Strict Definition)
- **$\ge 2$ ROIs**: ROI bootstrap.
- **$= 1$ ROI**: Adaptive grid block bootstrap with frozen features ($kNN$, $\tilde{u}_c$, $a(c)$). Output `UQ_mode=grid_block_frozen`.
- **Estimand**: Quantifies within-ROI resampling uncertainty.
- **Constraint**: Single-ROI variances are exclusively for patient-level UQ and cohort IVW weighting. They are STRICTLY PROHIBITED from participating in baseline $\lambda, \tau$ calibration.

## 3. Parameter Calibration Isolations
- **Calibration Pool**: Strictly `within-patient`, `baseline timepoint`, `same macro-compartment`.
- **Fallback Rule**: Patients with $<2$ baseline ROIs borrow group-level aggregated parameters and output audit fields (`n_pairs_calib`, `n_patients_calib`). No blind cross-patient pooling.

## 4. Drift as Risk Flagging
- **Rule**: $\Delta_{batch}$ must be derived from intra-timepoint batch contrasts to isolate treatment effects.
- **Usage**: Used purely for risk flagging (`drift-aligned = True`) and sensitivity analysis. No silent correction or overriding of matched mass.

## 5. Cohort-Level Inference (V2.0 Hurdle + ME Model)
- **Macro-Scale Conservation**: Report $\Delta \log S_{tumor}$ and $\Delta \log S_{stroma}$ to capture inter-compartment mass shifts.
- **Micro-Scale Models**: Hurdle + Measurement Error Joint Model.
  - **Zero-Component (Hurdle)**: Logistic regression on true biological clearances ($I_i$). Engineering zeros must be strictly filtered.
  - **Positive-Component (Likelihood)**: Continuous metric evaluation incorporating the log-scale empirical measurement error $s_i^2$ derived from the adaptive grid block bootstrap ($e_i \sim \mathcal{N}(0, \phi^2 + s_i^2)$).
- **Sensitivity**: Evaluation of parameter identifiability and robustness under varying numerical stabilizer bounds ($\delta$).

## 6. Biological & Clinical Concordance (Silver Standard Validation)
To establish the clinical utility and biological validity of the UOT metrics against the original TONIC findings, the following criteria must be evaluated:

### 6.1 Clinical Outcome Stratification via Unmatched Mass
- **Hypothesis**: Responders will exhibit significantly higher mass-normalized destruction ($d_{rel}$) in the `tumor` compartment, and significantly higher creation ($b_{rel}$) in the `stroma` or `interface` compartments compared to Non-responders.
- **Evidence**: Group-wise comparisons and IVW-adjusted forest plots.

### 6.2 Modeling Compartmental Collapse (Structural Zeros)
- **Hypothesis**: Responders have a significantly higher Odds Ratio (OR) of complete compartmental clearance ($I_{p,tumor} = 0$ at on-treatment), accurately captured by the existence component of the Two-Part Model.

### 6.3 Spatial Remapping and Biological Concordance
- **Hypothesis**: The highest-magnitude events (Top Remodeling Edges, Top Creation Prototypes) will physically colocalize at the tumor-stroma border. 
- **Evidence**: Projection of event masks onto physical coordinates $(x,y)$ to unsupervisedly mirror the original study's finding that immune infiltration at the tumor boundary dictates clinical response.

### 6.4 Robustness to Spatial Undersampling (Measurement Error Evaluation)
- **Hypothesis**: Incorporating single-ROI resampling variance directly into the likelihood as a measurement error ($s_i^2$) provides a more robust and statistically reliable clinical contrast than unweighted naive aggregation or heuristic IVW truncation.
- **Evidence**: Comparison of $p$-values, effect sizes, and residual homoscedasticity between a naive LMM (ignoring spatial uncertainty) and the Hurdle + Measurement Error joint model.

Adheres strictly to the structural zero bypass mechanism and uot_status data contract defined in V1.6 for missing compartments or shape-level dropouts.