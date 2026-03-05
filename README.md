# SLOTAR

**SLOTAR** = *Selection-aware Longitudinal Optimal Transport for Attribution & Remapping* A generic, mathematically rigorous framework for inferring physical transport dynamics and spatial sampling uncertainty in longitudinal or state-transition cohorts.

**Academic Positioning (V2.0)**: 
SLOTAR does not invent new spatial feature engineering or cell clustering methods. Instead, it takes any user-defined spatial state distributions (e.g., cell types, spatial communities) as **Prerequisite Inputs** and solves two critical inference challenges:
1. **Physical Transport under Mass Imbalance**: Using a batched, parameter-calibrated Unbalanced Optimal Transport (UOT) engine.
2. **Reliable Inference under Sampling Bias**: Using a Hurdle + Measurement Error joint likelihood model, robust to spatial undersampling without heuristic weight truncations.

This repository follows AVCP “repo-as-memory” conventions: decisions/specs live in versioned files under `docs/`, not chat context.

---

## Repository Architecture: Library vs Tasks (Hard Boundary)

This repo enforces a strict separation:

1) **`src/slotar/` (library-only)** Pure, reusable Python package implementing:
   - batched unbalanced optimal transport solver (log-domain, tensor-optimized)
   - uncertainty quantification primitives (adaptive block bootstrap, log-scale empirical variance $s_i^2$)
   - representation utilities (strictly treated as upstream prerequisite transformers)
   - drift **flagging** (consumer-only; no drift estimation)
   - I/O helpers (contracts-aware export)

   `src/slotar` knows nothing about “pCR”, “TONIC”, or any benchmark-specific orchestration.

2) **`tasks/` (task-scoped pipelines)**  
   End-to-end pipelines for each benchmark/case:
   - data loading / preprocessing
   - structural-zero bypass logic (Plan B)
   - drift vector construction or injection (if any)
   - cohort-level inference (two-part models, IVW) and figure generation

---

## Key AVCP Contracts (must read before coding)
Start each session by reading:
- `docs/state.md`
- `docs/constraints.md`
- `docs/decisions.md`
- `docs/api_specs.md`
- `docs/data_contracts.md`
- `docs/avcp_guidelines.md`

---

## Recommended Commands

```bash
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy .
pytest -q
````

---

## Notes

* Structural zeros are handled by **Plan B**:

  * `src/slotar` solver is **fail-fast** (raises `ValueError` on empty mass/support).
  * `tasks/*` pipelines are responsible for bypass and writing explicit NA + audit fields.
* Drift is **risk flagging only**. Drift vector estimation is never performed inside the library.