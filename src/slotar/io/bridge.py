from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Tuple

import pandas as pd
import yaml


def _get_logger() -> logging.Logger:
    logger = logging.getLogger("slotar.io.bridge")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


class DataContractError(ValueError):
    pass


def _load_config(config_path: Path) -> Dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    return cfg


def _resolve_output_dir(cfg: Dict[str, Any], config_path: Path) -> Path:
    configured = Path(cfg.get("paths", {}).get("interim_viz_dir", "data/interim_viz"))
    if configured.is_absolute():
        return configured
    # If config is at config/config.yaml, repo root is two levels up
    if config_path.as_posix().endswith("config/config.yaml"):
        repo_root = config_path.resolve().parents[1]
    else:
        repo_root = Path.cwd()
    return repo_root / configured


def _ensure_primary_key(df: pd.DataFrame, primary_key: str) -> pd.DataFrame:
    if primary_key in df.columns:
        return df
    # Create primary key from index
    out = df.reset_index(drop=False)
    if "index" in out.columns and primary_key not in out.columns:
        out = out.rename(columns={"index": primary_key})
    if primary_key not in out.columns:
        out.insert(0, primary_key, range(out.shape[0]))
    return out


def _validate_for_r_export(df: pd.DataFrame, primary_key: str) -> None:
    if primary_key not in df.columns:
        raise DataContractError(f"Missing primary key column: {primary_key}")
    if df[primary_key].isna().any():
        raise DataContractError("Primary key contains NA values")
    if df[primary_key].duplicated().any():
        raise DataContractError("Primary key contains duplicate values")


def save_for_r(
    df: pd.DataFrame,
    filename: str,
    config_path: str | Path = "config/config.yaml",
    primary_key: str = "row_id",
    provenance_script: str = "unknown",
    git_commit: str = "unknown",
) -> Tuple[Path, Path]:
    """
    Save a DataFrame for R visualization with a required meta sidecar.

    - Output dir: config.paths.interim_viz_dir (default: data/interim_viz)
    - Formats: .parquet or .csv
    - Enforces explicit primary key column; creates from index if missing
    - Writes *_meta.json with schema + provenance
    """
    logger = _get_logger()

    resolved_config_path = Path(config_path).resolve()
    cfg = _load_config(resolved_config_path)
    out_dir = _resolve_output_dir(cfg=cfg, config_path=resolved_config_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / filename
    suffix = out_path.suffix.lower()
    if suffix not in {".parquet", ".csv"}:
        raise DataContractError("filename must end with .parquet or .csv")

    df2 = _ensure_primary_key(df=df, primary_key=primary_key)
    _validate_for_r_export(df2, primary_key=primary_key)

    logger.info("Saving for R: rows=%s cols=%s -> %s", df2.shape[0], df2.shape[1], out_path)

    if suffix == ".parquet":
        df2.to_parquet(out_path, index=False)
    else:
        df2.to_csv(out_path, index=False)

    meta = {
        "file": out_path.name,
        "primary_key": primary_key,
        "columns": {col: str(dtype) for col, dtype in df2.dtypes.items()},
        "provenance": {
            "script": provenance_script,
            "git_commit": git_commit,
            "config": str(resolved_config_path),
        },
    }
    meta_path = out_path.with_name(f"{out_path.stem}_meta.json")
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    logger.info("Wrote meta sidecar: %s", meta_path)
    return out_path, meta_path