from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable

from bfrepricer.execution.intent import OrderIntent
from bfrepricer.execution.position import Position
from bfrepricer.domain.types import MarketId, SelectionId


@dataclass
class ExecutionEngine:
    positions: Dict[tuple[MarketId, SelectionId], Position] = field(default_factory=dict)

    def process(self, intents: Iterable[OrderIntent]) -> None:
        """
        Paper execution: assume immediate fill at quoted price.
        """
        for intent in intents:
            key = (intent.market_id, intent.selection_id)
            pos = self.positions.setdefault(key, Position())
            pos.apply_fill(intent.side, intent.price, intent.size)

    def snapshot(self) -> dict:
        """
        Lightweight snapshot for logging / debugging.
        """
        return {
            f"{m}:{s}": {
                "size": pos.size,
                "avg_price": round(pos.avg_price, 4),
                "realized_pnl": round(pos.realized_pnl, 4),
            }
            for (m, s), pos in self.positions.items()
        }
