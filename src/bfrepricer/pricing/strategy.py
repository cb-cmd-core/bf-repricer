from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from bfrepricer.execution.intent import IntentDecision, OrderIntent, Side
from bfrepricer.state.market_state import MarketSnapshot


@dataclass(frozen=True, slots=True)
class StrategyConfig:
    min_size: float = 2.0
    max_spread_ticks: float = 0.10  # rough sanity for UK horse odds
    stake_size: float = 2.0


class TopOfBookMicroStrategy:
    """
    Pure strategy: reads snapshot, returns intents.

    This is deliberately simple:
    - Only uses best_back / best_lay
    - Only emits a single small intent per tick (for now)
    - Good enough to validate the pipeline end-to-end
    """

    def __init__(self, config: StrategyConfig = StrategyConfig()) -> None:
        self._cfg = config

    def decide(self, snap: MarketSnapshot) -> IntentDecision:
        intents: list[OrderIntent] = []

        # Pick first runner that has both sides of book
        for sel_id, rb in snap.runners.items():
            if rb.best_back is None or rb.best_lay is None:
                continue

            back = rb.best_back
            lay = rb.best_lay

            # basic sanity checks
            if back.size < self._cfg.min_size or lay.size < self._cfg.min_size:
                continue

            spread = lay.price - back.price
            if spread <= 0 or spread > self._cfg.max_spread_ticks:
                continue

            # naive "micro" intent: back at best_back (paper-safe)
            intents.append(
                OrderIntent(
                    market_id=snap.market_id,
                    selection_id=sel_id,
                    side=Side.BACK,
                    price=back.price,
                    size=self._cfg.stake_size,
                    reason=f"top-of-book back; spread={spread:.3f}",
                )
            )
            break  # single-intent policy for now

        notes = "no actionable intent" if not intents else "ok"
        return IntentDecision(intents=intents, notes=notes)
