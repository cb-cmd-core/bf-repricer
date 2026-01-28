from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict

from bfrepricer.domain.events import MarketTick
from bfrepricer.domain.types import MarketId, RunnerBook, SelectionId, utc_now


class StaleMarketData(RuntimeError):
    pass


class OutOfOrderTick(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    market_id: MarketId
    last_seq: int
    last_publish_time: datetime
    is_market_open: bool | None
    runners: Dict[SelectionId, RunnerBook]


class MarketState:
    """
    Maintains in-memory state for a single market.

    Invariants:
    - seq is monotonically increasing (idempotent on duplicates)
    - last_publish_time moves forward (or stays same on duplicate)
    - updates are merge-based (partial runner updates OK)
    - "fail closed": staleness check can disable execution upstream
    """

    def __init__(self, market_id: MarketId) -> None:
        self._market_id = market_id
        self._last_seq: int = -1
        self._last_publish_time: datetime | None = None
        self._is_market_open: bool | None = None
        self._runners: Dict[SelectionId, RunnerBook] = {}

    @property
    def market_id(self) -> MarketId:
        return self._market_id

    @property
    def last_seq(self) -> int:
        return self._last_seq

    @property
    def last_publish_time(self) -> datetime | None:
        return self._last_publish_time

    @property
    def is_market_open(self) -> bool | None:
        return self._is_market_open

    def apply(self, tick: MarketTick) -> None:
        if tick.market_id != self._market_id:
            raise ValueError(f"tick market_id {tick.market_id} != state market_id {self._market_id}")

        # Idempotent on duplicates
        if tick.seq == self._last_seq:
            return

        # Enforce monotonic ordering (critical for correctness)
        if tick.seq < self._last_seq:
            raise OutOfOrderTick(f"tick seq {tick.seq} < last_seq {self._last_seq}")

        # Apply tick
        self._last_seq = tick.seq
        self._last_publish_time = tick.publish_time
        if tick.is_market_open is not None:
            self._is_market_open = tick.is_market_open

        # Merge runner updates
        for rb in tick.runners:
            self._runners[rb.selection_id] = rb

    def snapshot(self) -> MarketSnapshot:
        if self._last_publish_time is None:
            # Not yet initialized; treat as empty but identifiable
            return MarketSnapshot(
                market_id=self._market_id,
                last_seq=self._last_seq,
                last_publish_time=datetime.fromtimestamp(0, tz=utc_now().tzinfo),
                is_market_open=self._is_market_open,
                runners=dict(self._runners),
            )

        return MarketSnapshot(
            market_id=self._market_id,
            last_seq=self._last_seq,
            last_publish_time=self._last_publish_time,
            is_market_open=self._is_market_open,
            runners=dict(self._runners),
        )

    def assert_fresh(self, *, max_age: timedelta) -> None:
        """
        Used by pricing/execution guards.
        Raises if we haven't received a tick recently.
        """
        if self._last_publish_time is None:
            raise StaleMarketData("no ticks received yet")

        age = utc_now() - self._last_publish_time
        if age > max_age:
            raise StaleMarketData(f"market data stale: age={age} max_age={max_age}")
