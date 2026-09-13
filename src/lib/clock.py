"""Injectable clock. Telemetry timestamps are Asia/Hong_Kong.

OBSERVABILITY HOOK — ``LLMCallTelemetry.timestamp``
---------------------------------------------------
Constitution tests pin ``datetime(2026, 9, 11, 12, 0, tzinfo=HKT)``. A wall
clock would make T0.1 flake. ``structlog.TimeStamper`` stays UTC ISO; do not
assert those two clocks are equal (architecture §4.1).

This is the same injectable-clock pattern as cec-vivisystem. The LLM is not
allowed to be the source of "now".
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from zoneinfo import ZoneInfo

FAMILY_TZ = ZoneInfo("Asia/Hong_Kong")


class Clock:
    """``now()`` returns a timezone-aware datetime in ``Asia/Hong_Kong``."""

    def __init__(self, now_fn: Callable[[], datetime] | None = None) -> None:
        self._now_fn = now_fn

    def now(self) -> datetime:
        if self._now_fn is not None:
            value = self._now_fn()
        else:
            value = datetime.now(tz=FAMILY_TZ)
        if value.tzinfo is None:
            return value.replace(tzinfo=FAMILY_TZ)
        return value.astimezone(FAMILY_TZ)
