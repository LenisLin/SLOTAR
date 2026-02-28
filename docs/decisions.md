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