"""Exponential-backoff retry for outbound HTTP calls made by job handlers.

Kept from the previous runner; the new handlers are expected to wrap their calls in this.
"""
from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def with_backoff(fn: Callable[[], T], attempts: int = 5, base: float = 0.5) -> T:
    last: Exception | None = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(base * (2**i))
    assert last is not None
    raise last
