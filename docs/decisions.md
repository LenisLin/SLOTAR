# Decisions

## D001 — SLOTAR V1.5 Core Algorithm Architecture
- **Context**: Longitudinal spatial omics data (e.g., IMC) suffers from structural asymmetry (unmatched mass) due to sampling bias and true biological remodeling (e.g., pCR vs NR in gastric cancer). Traditional paired tests fail under these conditions.
- **Decision**: Adopt the SLOTAR V1.5 framework as the mathematical engine.
  - Use community prototypes (kNN + block-wise robust scaling + k-means) to establish a unified semantic space.
  - Decouple spatial changes into Density-level, Shape-level, and Scale ratio.
  - Employ Unbalanced Optimal Transport (UOT) with generalized KL divergence and entropic regularization ($\varepsilon$-scaling) to attribute changes to Retention, Remodeling, Creation, and Destruction.
  - Implement adaptive grid ($G \times G$) composition-stratified Block Bootstrap for single-ROI uncertainty quantification.
  - Enforce a global static cost scaling factor ($s_C$) to ensure $\lambda$ comparability across calibrations and inferences.
- **Alternatives Rejected**: 
  - Standard Balanced OT (rejected due to inability to handle unmatched mass like tissue creation/destruction).
  - Pure $2 \times 2$ static block bootstrap for single ROI (rejected due to statistical collapse/zero-variance false confidence).
  - Dynamic median cost scaling per UOT instance (rejected due to dimensional distortion of $\lambda$).
- **Consequences**: This mathematically bounds the problem and guarantees solvability, but requires rigorous $\varepsilon$-scaling and log-domain Sinkhorn implementations to prevent numerical underflow in sparse high-dimensional data.
- **Review Trigger**: If UOT solver fails to converge on real IMC data, or if block bootstrap yields undefined confidence intervals.

### V1.5 Algorithm Pseudocode (Locked Blueprint)
*(Refer to the agreed Proposal V1.5 for the full specifications of Algorithm 1: End-to-end, Algorithm 2: Group-wise calibration, and Algorithm 3: SolveUOT + Decompose)*

## D002 — SLOTAR V1.6 Core Algorithm Architecture Upgrade
- Context: V1.5 metrics (L1 distance, absolute density, arbitrary tau) lacked strict physical units, tightly bounded unmatched mass extraction, and robust single-ROI topology preservation.
- Decision: Upgrade to V1.6 mathematical engine.
  1. **Area-weighted aggregation**: Use $\frac{\sum N}{\sum Area}$ for density to ensure strict cells/mm² physics semantics.
  2. **Positive-part metrics**: Use $(x-m)_+$ for Creation/Destruction to accurately isolate unmatched mass under UOT KL relaxation.
  3. **Group-wise calibration**: Implement baseline calibration for $\tau_g$ (Retention threshold) using pre ROI-ROI pairs within the same group.
  4. **Active set separation**: Decouple semantic pruning (tracked explicitly by `mass_pruned_ratio`) from numerical stability limits (`eta_floor`).
  5. **Frozen-feature Bootstrap**: Enforce single-ROI adaptive grid block bootstrap with frozen kNN/prototypes to prevent topological tearing.
- Alternatives: L1 metrics (rejected due to confounding marginal relaxation with creation), moving-block bootstrap (kept as secondary option, too complex for default).
- Consequences: Output data contracts must be strictly expanded to include mandatory audit fields (`mass_pruned_ratio`, `eps_schedule_id`, etc.) to guarantee traceability and reproducibility.
- Review Trigger: Failure of log-domain Sinkhorn convergence or unacceptable `mass_pruned_ratio` (>0.5%) triggering sensitivity degradation.

## D004 — Hard Boundary Isolation (Library vs. Tasks)
- **Context**: To maintain the pure mathematical rigor of the UOT solver and prevent overfitting to specific benchmark cohorts, the core engine and clinical inferences must be physically separated.
- **Decision**: Enforce a strict physical boundary. `src/slotar/` operates strictly as a domain-agnostic mathematical library (UOT, representation, UQ primitives). All clinical logic, cohort-level inferences, explicit loopings, and biological evaluation (drift vector estimation) are strictly confined to the `tasks/` directory.
- **Consequences**: Any benchmark-specific logic bleeding into `src/slotar/` will fail CI/CD. The core library takes representations as prerequisites and holds no knowledge of clinical metadata.

## D005 — Batched Unbalanced Optimal Transport (Engineering Throughput)
- **Context**: The existing Python `for`-loop over bootstrap replicates and $\lambda$ candidate grids introduces unacceptable overhead, leading to severe computational bottlenecks for large cohorts.
- **Decision**: Upgrade the mathematical engine to a tensor-based Batched Unbalanced Log-domain Sinkhorn solver. The pipeline must construct `[N, K]` tensors to execute UOT solves simultaneously across batch dimensions (patients, lambdas, or replicates).
- **Constraints**: This is strictly an engineering optimization. The mathematical estimands, baseline calibration rules, and fail-fast behaviors must remain strictly equivalent to V1.6.

## D006 — Hurdle + Measurement Error Joint Model (SLOTAR V2.0 Inference)
- **Context**: Traditional Inverse Variance Weighting (IVW) on aggregated UQ estimates suffers from severe instability ("weight explosion") when local variance $\sigma_i^2$ approaches zero, and requires heuristic truncations that alter the inference estimand.
- **Decision**: Adopt a Hurdle + Measurement Error Joint Model. The parameter estimate $\hat{\theta}_i$ and its bootstrap-derived uncertainty are ingested directly into the likelihood function as a measurement error component $e_i \sim \mathcal{N}(0, \phi^2 + s_i^2)$.
- **Constraints (Locked)**:
  1. **Log-scale Empirical Variance**: $s_i^2$ must be computed empirically on the log-transformed bootstrap replicates: $s_i^2 := \text{Var}(\log(\hat{\theta}_i^{(b)} + \delta))$, not via Delta method on infinitesimal point estimates.
  2. **Numerical Stabilizer Bounds**: A strict numerical lower bound (`s2_lower_bound`) must be enforced on $s_i^2$ to prevent underestimation of total uncertainty.
  3. **Identifiability Diagnostics**: The pipeline must evaluate the heterogeneity of the $\{s_i^2\}$ distribution before drawing inference claims.
  4. **Strict Zero Stratification**: Only biologically justified "True Zeros" (e.g., compartment collapse) may enter the hurdle model's zero component. Engineering failures or pruning-induced zeros must be strictly logged as `NaN` (Missing Data).
  5. **Bias-Variance Boundary**: This model absorbs sampling variance, not systemic sampling bias.