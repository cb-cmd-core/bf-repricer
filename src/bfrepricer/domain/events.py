from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .types import MarketId, RunnerBook


@dataclass(frozen=True, slots=True)
class MarketTick:
    """
    Normalized event representing "the market changed".

    seq: monotonic sequence per market
    publish_time: UTC time tick observed/published
    runners: partial or full runner updates (merged into state)
    is_market_open: True=open, False=suspended/closed-ish, None=unknown
    is_in_play: True if market has turned in-play (irreversible)
    is_closed: True if market is closed (terminal)
    """
    market_id: MarketId
    seq: int
    publish_time: datetime
    runners: tuple[RunnerBook, ...]
    is_market_open: bool | None = None
    is_in_play: bool | None = None
    is_closed: bool | None = None
