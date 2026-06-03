"""
Centralized logging configuration.

Uses Python's built-in logging module.  Logs go to both stdout and a rotating
file under the data directory.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(
    log_level: str = "INFO",
    log_file: Path | None = None,
) -> logging.Logger:
    """Configure the root logger with console + file handlers.

    Args:
        log_level: One of DEBUG, INFO, WARNING, ERROR, CRITICAL.
        log_file: Optional path to a log file.  If None, no file logging.

    Returns:
        The configured root logger.
    """
    logger = logging.getLogger("desktop_pet")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Prevent duplicate handlers on repeated setup_logging calls
    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    logger.addHandler(console)

    # File handler (optional)
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            str(log_file),
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a child logger under the 'desktop_pet' namespace."""
    return logging.getLogger(f"desktop_pet.{name}")
