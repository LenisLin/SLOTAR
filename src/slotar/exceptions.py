"""
Module: src.slotar.exceptions
Architecture: Library Level
Constraints:
- Defines canonical string constants for data-level UOT status isolation.
- Defines Exception classes for programmer-level constraint violations.
- STRICTLY NO dynamic error generation or Enums that wrap values obscurely 
  (must maintain NumPy object string array safety).
"""
from __future__ import annotations

# ---- Data-Level Degeneracy Status Codes ----
# Used exclusively for the `status` array in batched operations.
ERR_UOT_EMPTY_MASS_SOURCE: str = "ERR_UOT_EMPTY_MASS_SOURCE"
ERR_UOT_EMPTY_MASS_TARGET: str = "ERR_UOT_EMPTY_MASS_TARGET"
ERR_UOT_EMPTY_SUPPORT: str = "ERR_UOT_EMPTY_SUPPORT"
ERR_UOT_NUMERICAL: str = "ERR_UOT_NUMERICAL"

# ---- Programmer-Level Exceptions ----
class UOTInputError(ValueError):
    """Raised strictly for legacy single-item API or non-batchable programmer errors."""
    pass

# Note: DataContractError is defined in contracts.py to prevent circular imports,
# but can be imported here if centralizing is preferred.
