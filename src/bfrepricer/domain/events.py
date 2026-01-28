from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .types import MarketId, RunnerBook


@dataclass(frozen=True, slots=True)
class MarketTick:
    """
    Normalized, minimal event representing "the market changed".

    seq: Monotonic sequence per market (from stream), used to enforce idempotence.
    publish_time: When the tick was observed/published (UTC).
    runners: Partial or full runner updates (we merge into state).
    is_market_open: Best-effort indicator; treat unknown transitions cautiously.
    """
    market_id: MarketId
    seq: int
    publish_time: datetime
    runners: tuple[RunnerBook, ...]
    is_market_open: bool | None = None
