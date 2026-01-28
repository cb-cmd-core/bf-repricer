from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from bfrepricer.domain.types import MarketId, SelectionId
from bfrepricer.execution.intent import OrderIntent
from bfrepricer.execution.position import Position


@dataclass(frozen=True)
class RiskConfig:
    max_abs_pos_per_selection: float = 10.0
    max_abs_pos_per_market: float = 30.0
    max_order_size: float = 2.0


@dataclass
class RiskGate:
    cfg: RiskConfig

    def filter_intents(
        self,
        *,
        intents: Iterable[OrderIntent],
        positions: Dict[Tuple[MarketId, SelectionId], Position],
    ) -> List[OrderIntent]:
        """
        Returns a filtered/clamped list of intents.

        Invariants:
        - Never increase exposure beyond caps.
        - Always allow position-reducing intents (risk-off).
        - Fail closed: if anything is ambiguous, drop the intent.
        """
        out: List[OrderIntent] = []

        # Precompute market abs exposure
        market_abs: Dict[MarketId, float] = {}
        for (m, _s), pos in positions.items():
            market_abs[m] = market_abs.get(m, 0.0) + abs(pos.size)

        for i in intents:
            # Clamp single order size
            size = min(float(i.size), float(self.cfg.max_order_size))
            if size <= 0:
                continue

            key = (i.market_id, i.selection_id)
            pos = positions.get(key, Position())

            # Signed delta: BACK increases long, LAY increases short
            signed = size if i.side.value == "BACK" else -size

            # Determine whether this intent increases or reduces absolute exposure
            before = pos.size
            after = before + signed

            reduces_abs = abs(after) < abs(before)

            if reduces_abs:
                # Always allow risk-off. Still clamp size.
                out.append(i.__class__(
                    market_id=i.market_id,
                    selection_id=i.selection_id,
                    side=i.side,
                    price=i.price,
                    size=size,
                    reason=i.reason + " | risk:allow_reduce",
                ))
                # Update temp positions for subsequent intents in this batch
                pos2 = Position(size=before, avg_price=pos.avg_price, realized_pnl=pos.realized_pnl)
                pos2.size = after
                positions[key] = pos2
                market_abs[i.market_id] = market_abs.get(i.market_id, 0.0) - abs(before) + abs(after)
                continue

            # Increasing exposure: enforce caps

            # Per-selection cap
            if abs(after) > self.cfg.max_abs_pos_per_selection:
                continue

            # Per-market cap (approx, using abs position)
            current_market_abs = market_abs.get(i.market_id, 0.0)
            projected_market_abs = current_market_abs - abs(before) + abs(after)
            if projected_market_abs > self.cfg.max_abs_pos_per_market:
                continue

            out.append(i.__class__(
                market_id=i.market_id,
                selection_id=i.selection_id,
                side=i.side,
                price=i.price,
                size=size,
                reason=i.reason + " | risk:ok",
            ))

            # Update temp tracking so multiple intents in a tick don't exceed caps
            pos2 = Position(size=before, avg_price=pos.avg_price, realized_pnl=pos.realized_pnl)
            pos2.size = after
            positions[key] = pos2
            market_abs[i.market_id] = projected_market_abs

        return out
