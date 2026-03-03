from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UOTErrorCode:
    """Canonical error codes for fail-fast UOT input validation."""
    code: str


ERR_UOT_EMPTY_MASS_SOURCE = UOTErrorCode("ERR_UOT_EMPTY_MASS_PRE")
ERR_UOT_EMPTY_MASS_TARGET = UOTErrorCode("ERR_UOT_EMPTY_MASS_POST")
ERR_UOT_EMPTY_SUPPORT = UOTErrorCode("ERR_UOT_EMPTY_SUPPORT")


class UOTInputError(ValueError):
    """Fail-fast error for invalid UOT inputs (Plan B)."""

    def __init__(self, code: UOTErrorCode, message: str) -> None:
        super().__init__(f"{code.code}: {message}")
        self.code = code