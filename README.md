# SLOTAR

**SLOTAR** = *Selection-aware Longitudinal Optimal Transport for Attribution & Remapping*  
A contract-first, reproducible framework for multi-ROI spatial omics (IMC / ST) longitudinal or state-transition analysis.

This repository follows AVCP “repo-as-memory” conventions: decisions/specs live in versioned files under `docs/`, not chat context.

---

## Repository Architecture: Library vs Tasks (Hard Boundary)

This repo enforces a strict separation:

1) **`src/slotar/` (library-only)**  
   Pure, reusable Python package implementing:
   - representation / prototypes / cost scaling
   - UOT solver + metrics + events (math engine)
   - uncertainty quantification primitives (bootstrap)
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