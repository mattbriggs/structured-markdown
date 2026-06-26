"""Structured logging configuration for structure_parser."""
from __future__ import annotations

import logging
import sys

try:
    from pythonjsonlogger import jsonlogger  # type: ignore[import]
    _JSON_LOGGER_AVAILABLE = True
except ImportError:
    _JSON_LOGGER_AVAILABLE = False

_LOGGER_NAME = "structure_parser"


def configure_logging(debug: bool = False, json_output: bool = False) -> None:
    """Configure the structure_parser logger.

    :param debug: Enable DEBUG level logging when True; INFO otherwise.
    :param json_output: Emit structured JSON log lines when True.
    """
    logger = logging.getLogger(_LOGGER_NAME)
    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)

    if logger.handlers:
        logger.handlers.clear()

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)

    if json_output and _JSON_LOGGER_AVAILABLE:
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        )
    else:
        formatter = logging.Formatter(
            fmt="%(levelname)s [%(name)s] %(message)s",
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a child logger under the structure_parser namespace."""
    return logging.getLogger(f"{_LOGGER_NAME}.{name}" if name else _LOGGER_NAME)
