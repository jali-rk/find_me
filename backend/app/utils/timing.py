"""
Timing utilities for performance measurement.
"""

import time
from contextlib import contextmanager
from typing import Generator

from app.core.logging import get_logger

logger = get_logger(__name__)


@contextmanager
def timing(operation: str) -> Generator[None, None, None]:
    """
    Context manager to log execution time of an operation.

    Args:
        operation: Description of the operation being timed

    Usage:
        with timing("face detection"):
            detect_faces(image)
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        logger.info(f"{operation} took {elapsed:.3f}s")


def current_timestamp() -> float:
    """Get current Unix timestamp in seconds."""
    return time.time()
