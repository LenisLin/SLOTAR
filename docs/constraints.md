# Constraints (Locked)

C1. Repo-as-memory: locked constraints live here; undocumented constraints are not binding.
C2. Strict Configuration Decoupling: The library layer (src/slotar/) is STRICTLY FORBIDDEN from importing yaml or reading config.yaml. All paths, hyperparameters, and configurations must be explicitly passed as function arguments from the tasks/ layer.
C3. No silent failures: logging + validation + fail-fast assertions are mandatory. Specifically, structural zeros or empty mathematical supports MUST trigger a fail-fast Exception in low-level engines, or be explicitly bypassed with structured audit logs at the pipeline level. Numerical padding (e.g., adding epsilon to empty vectors to force convergence) is strictly forbidden.
C4. No speculative science: uncertain algorithms/metrics must go through Tier-2 gate.
C5. Python→R bridge: any handover file must be created via save_for_r() in src/slotar/io/bridge.py.
C6. Domain-Logic Isolation (Library vs. Tasks): `src/slotar` MUST remain a domain-agnostic math and algorithm library. All cohort-level inferences (e.g., Two-part models, IVW, LMM), explicit clinical looping (patient/visit iteration), and automated biological evaluations (e.g., drift vector estimation, automatic clustering) MUST be implemented strictly within the respective `tasks/<task_name>/pipeline.py` or associated task scripts.

# Versioning Model (Lock one)
# - Model A: single repo SemVer
# - Model B: component SemVer
# - Model C: single repo SemVer + API_VERSION
