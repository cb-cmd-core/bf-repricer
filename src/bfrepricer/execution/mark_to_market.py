from __future__ import annotations

from bfrepricer.execution.position import Position
from bfrepricer.domain.types import PriceSize


def mark_to_market(position: Position, *, best_back: PriceSize | None, best_lay: PriceSize | None) -> float:
    """
    Compute unrealized PnL using top-of-book opposing side.

    Long  -> mark on best LAY
    Short -> mark on best BACK
    """
    if position.size == 0:
        return 0.0

    if position.size > 0:
        if best_lay is None:
            return 0.0
        mark_price = best_lay.price
    else:
        if best_back is None:
            return 0.0
        mark_price = best_back.price

    return position.size * (mark_price - position.avg_price)
