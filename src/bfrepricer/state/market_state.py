from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict

from bfrepricer.domain.events import MarketTick
from bfrepricer.domain.regime import MarketRegime
from bfrepricer.domain.types import MarketId, RunnerBook, SelectionId, utc_now


class StaleMarketData(RuntimeError):
    pass


class OutOfOrderTick(RuntimeError):
    pass


class UnsafeMarketRegime(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    market_id: MarketId
    last_seq: int
    last_publish_time: datetime
    regime: MarketRegime
    runners: Dict[SelectionId, RunnerBook]


class MarketState:
    """
    In-memory state + regime tracker for a single market.

    Invariants:
    - seq is monotonic (idempotent on duplicates)
    - regime transitions are explicit
    - execution is disabled outside OPEN
    """

    def __init__(self, market_id: MarketId) -> None:
        self._market_id = market_id
        self._last_seq: int = -1
        self._last_publish_time: datetime | None = None
        self._regime: MarketRegime = MarketRegime.UNKNOWN
        self._runners: Dict[SelectionId, RunnerBook] = {}

    def apply(self, tick: MarketTick) -> None:
        if tick.market_id != self._market_id:
            raise ValueError("tick market_id mismatch")

        if tick.seq == self._last_seq:
            return

        if tick.seq < self._last_seq:
            raise OutOfOrderTick(f"{tick.seq=} < {self._last_seq=}")

        self._last_seq = tick.seq
        self._last_publish_time = tick.publish_time

        # --- Regime inference (conservative) ---
        if tick.is_market_open is True:
            if self._regime in {MarketRegime.UNKNOWN, MarketRegime.SUSPENDED}:
                self._regime = MarketRegime.OPEN
        elif tick.is_market_open is False:
            # Could be suspended or closed; treat as SUSPENDED unless explicitly closed later
            self._regime = MarketRegime.SUSPENDED

        # Merge runners
        for rb in tick.runners:
            self._runners[rb.selection_id] = rb

    def assert_fresh(self, *, max_age: timedelta) -> None:
        if self._last_publish_time is None:
            raise StaleMarketData("no ticks yet")

        age = utc_now() - self._last_publish_time
        if age > max_age:
            raise StaleMarketData(f"stale data: {age}")

    def can_execute(self) -> bool:
        """
        Hard execution gate.
        Only OPEN is allowed.
        """
        return self._regime == MarketRegime.OPEN

    def assert_safe_to_execute(self) -> None:
        if not self.can_execute():
            raise UnsafeMarketRegime(f"cannot execute in regime {self._regime}")

    def snapshot(self) -> MarketSnapshot:
        return MarketSnapshot(
            market_id=self._market_id,
            last_seq=self._last_seq,
            last_publish_time=self._last_publish_time or datetime.fromtimestamp(0),
            regime=self._regime,
            runners=dict(self._runners),
        )
