"""Structured, per-step application logging."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def build_step_logger(log_directory: Path) -> logging.Logger:
    log_directory.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("mandi_mitra.steps")
    if not logger.handlers:
        handler = logging.FileHandler(log_directory / "pipeline_steps.jsonl", encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def log_step(logger: logging.Logger, step: str, payload: dict[str, Any]) -> None:
    logger.info(json.dumps({"timestamp": datetime.now(timezone.utc).isoformat(), "step": step, **payload}))
