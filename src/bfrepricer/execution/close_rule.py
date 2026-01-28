from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from bfrepricer.domain.types import MarketId, SelectionId
from bfrepricer.execution.intent import OrderIntent, Side
from bfrepricer.execution.position import Position
from bfrepricer.domain.types import RunnerBook


@dataclass(frozen=True)
class CloseRuleConfig:
    take_profit_delta: float = 0.10  # price move in our favor
    stop_loss_delta: float = 0.10    # price move against us


@dataclass
class CloseRule:
    cfg: CloseRuleConfig

    def decide_closes(
        self,
        *,
        market_id: MarketId,
        runners: Dict[SelectionId, RunnerBook],
        positions: Dict[Tuple[MarketId, SelectionId], Position],
    ) -> List[OrderIntent]:
        intents: List[OrderIntent] = []

        for (m, sel), pos in positions.items():
            if m != market_id:
                continue
            if pos.size == 0:
                continue

            rb = runners.get(sel)
            if rb is None:
                continue

            # Determine mark + close side
            if pos.size > 0:
                # long -> close via LAY; mark using best_lay
                if rb.best_lay is None:
                    continue
                mark = rb.best_lay.price
                close_side = Side.LAY
                edge = mark - pos.avg_price
                close_price = rb.best_lay.price
                close_size = abs(pos.size)
            else:
                # short -> close via BACK; mark using best_back
                if rb.best_back is None:
                    continue
                mark = rb.best_back.price
                close_side = Side.BACK
                edge = pos.avg_price - mark
                close_price = rb.best_back.price
                close_size = abs(pos.size)

            if edge >= self.cfg.take_profit_delta:
                intents.append(
                    OrderIntent(
                        market_id=market_id,
                        selection_id=sel,
                        side=close_side,
                        price=close_price,
                        size=close_size,
                        reason=f"close_rule: take_profit edge={edge:.3f}",
                    )
                )
            elif edge <= -self.cfg.stop_loss_delta:
                intents.append(
                    OrderIntent(
                        market_id=market_id,
                        selection_id=sel,
                        side=close_side,
                        price=close_price,
                        size=close_size,
                        reason=f"close_rule: stop_loss edge={edge:.3f}",
                    )
                )

        return intents
