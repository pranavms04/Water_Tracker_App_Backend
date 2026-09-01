"""Logging configuration for WaterTrack application."""

import logging
import sys


def setup_logging(log_level: str = "INFO") -> None:
    """Configures structured logging across the application."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


logger = logging.getLogger("watertrack")
