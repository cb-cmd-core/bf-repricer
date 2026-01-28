from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
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
    cooldown_until: datetime | None
    runners: Dict[SelectionId, RunnerBook]


class MarketState:
    """
    Market state with explicit regime tracking + reopen cooldown + in-play lockout.

    Execution rules:
    - Only OPEN markets may execute
    - After reopening, execution blocked until cooldown expires
    - If market becomes IN_PLAY, execution is disabled permanently for this instance
    - Fail closed by default
    """

    def __init__(
        self,
        market_id: MarketId,
        *,
        reopen_cooldown: timedelta = timedelta(seconds=2),
    ) -> None:
        self._market_id = market_id
        self._last_seq: int = -1
        self._last_publish_time: datetime | None = None
        self._regime: MarketRegime = MarketRegime.UNKNOWN
        self._runners: Dict[SelectionId, RunnerBook] = {}

        self._reopen_cooldown = reopen_cooldown
        self._cooldown_until: datetime | None = None

    def apply(self, tick: MarketTick) -> None:
        if tick.market_id != self._market_id:
            raise ValueError("tick market_id mismatch")

        if tick.seq == self._last_seq:
            return

        if tick.seq < self._last_seq:
            raise OutOfOrderTick(f"{tick.seq=} < {self._last_seq=}")

        self._last_seq = tick.seq
        self._last_publish_time = tick.publish_time

        # --- IN_PLAY is a hard regime lockout ---
        if tick.is_in_play is True:
            self._regime = MarketRegime.IN_PLAY

        # If already in-play, do not allow any other regime changes back to OPEN.
        if self._regime != MarketRegime.IN_PLAY:
            prev_regime = self._regime

            if tick.is_market_open is True:
                if prev_regime in {MarketRegime.SUSPENDED, MarketRegime.UNKNOWN}:
                    self._cooldown_until = tick.publish_time + self._reopen_cooldown
                self._regime = MarketRegime.OPEN

            elif tick.is_market_open is False:
                self._regime = MarketRegime.SUSPENDED

        # Merge runner updates
        for rb in tick.runners:
            self._runners[rb.selection_id] = rb

    def assert_fresh(self, *, max_age: timedelta) -> None:
        if self._last_publish_time is None:
            raise StaleMarketData("no ticks received")

        age = utc_now() - self._last_publish_time
        if age > max_age:
            raise StaleMarketData(f"stale data: {age}")

    def can_execute(self, *, now: datetime | None = None) -> bool:
        if self._regime != MarketRegime.OPEN:
            return False

        if self._cooldown_until is None:
            return True

        now = now or utc_now()
        return now >= self._cooldown_until

    def assert_safe_to_execute(self, *, now: datetime | None = None) -> None:
        if not self.can_execute(now=now):
            raise UnsafeMarketRegime(
                f"unsafe to execute: regime={self._regime}, cooldown_until={self._cooldown_until}"
            )

    def snapshot(self) -> MarketSnapshot:
        return MarketSnapshot(
            market_id=self._market_id,
            last_seq=self._last_seq,
            last_publish_time=self._last_publish_time
            or datetime.fromtimestamp(0, tz=timezone.utc),
            regime=self._regime,
            cooldown_until=self._cooldown_until,
            runners=dict(self._runners),
        )
