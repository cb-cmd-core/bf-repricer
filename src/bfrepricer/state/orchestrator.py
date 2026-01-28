from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable

from bfrepricer.domain.events import MarketTick
from bfrepricer.domain.regime import MarketRegime
from bfrepricer.domain.types import MarketId
from bfrepricer.state.market_state import MarketState, MarketSnapshot


@dataclass(frozen=True, slots=True)
class ClosedMarket:
    market_id: MarketId
    snapshot: MarketSnapshot


class MarketOrchestrator:
    """
    Owns lifecycle of MarketState objects.

    Policies:
    - MarketState is created on first tick
    - CLOSED markets are evicted immediately after closure
    - Final snapshot is returned for downstream handling (logging, persistence)
    """

    def __init__(self) -> None:
        self._markets: Dict[MarketId, MarketState] = {}

    def active_market_ids(self) -> Iterable[MarketId]:
        return self._markets.keys()

    def apply(self, tick: MarketTick) -> ClosedMarket | None:
        """
        Apply a tick to its market.

        Returns:
            ClosedMarket if this tick caused the market to close,
            otherwise None.
        """
        state = self._markets.get(tick.market_id)
        if state is None:
            state = MarketState(tick.market_id)
            self._markets[tick.market_id] = state

        state.apply(tick)

        snap = state.snapshot()
        if snap.regime == MarketRegime.CLOSED:
            # Evict immediately
            del self._markets[tick.market_id]
            return ClosedMarket(
                market_id=tick.market_id,
                snapshot=snap,
            )

        return None

    def get(self, market_id: MarketId) -> MarketState | None:
        return self._markets.get(market_id)
