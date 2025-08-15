"""Path helpers for common directories."""

from __future__ import annotations

from pathlib import Path

from config import get_settings


def data_dir() -> Path:
    """Return the data directory path."""
    return Path(get_settings().DATA_DIR)


def log_dir() -> Path:
    """Return the log directory path."""
    return Path(get_settings().LOG_DIR)


def tmp_dir() -> Path:
    """Return the temporary directory path."""
    return Path(get_settings().TMP_DIR)
