"""
Module: src.slotar.io.bridge
Architecture: Library Level (I/O & Export)
Constraints:
- STRICTLY NO `yaml` imports or config parsing.
- Paths and audit metadata must be explicitly provided by the caller (tasks layer).
- Must enforce output data contracts before writing to disk.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

# 延迟或直接导入 Step 1 中定义的契约验证器
from ..contracts import validate_events_table, validate_metrics_table


def save_for_r(
    metrics_df: pd.DataFrame,
    events_df: pd.DataFrame,
    output_dir: str | Path,
    meta_audit: dict[str, Any],
) -> None:
    """
    Exports SLOTAR results (metrics and events) to disk for downstream R analysis,
    strictly enforcing data contracts before writing.

    Args:
        metrics_df: DataFrame containing patient/group level metrics and statuses.
        events_df: DataFrame containing micro-level transport events.
        output_dir: Target directory for export. Must be created if it doesn't exist.
        meta_audit: Dictionary containing global audit fields (e.g., s_C, UQ_mode, thresholds).

    Side Effects:
        - Writes `metrics_.csv` to `output_dir`.
        - Writes `events_.parquet` to `output_dir`.
        - Writes `meta_.json` to `output_dir`.

    Constraints for Codex:
        1. CONFIG ISOLATION: You MUST NOT import `yaml` or attempt to read any `config.yaml`. 
           Use the `output_dir` provided in the arguments exclusively.
        2. CONTRACT ENFORCEMENT: You MUST call `validate_metrics_table(metrics_df)` and 
           `validate_events_table(events_df)` BEFORE any file operations. Let DataContractError 
           propagate if validation fails.
        3. META SIDECAR: You MUST inject `{"schema_version": "v2.0"}` into the `meta_audit` 
           dictionary (if not already present) and export it cleanly via `json.dump`.
    """
    raise NotImplementedError(
        "Codex: Implement the contract-aware export logic here. Enforce absolute config decoupling."
    )