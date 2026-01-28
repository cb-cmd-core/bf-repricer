from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import NewType

MarketId = NewType("MarketId", str)
SelectionId = NewType("SelectionId", int)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class PriceSize:
    price: float
    size: float

    def __post_init__(self) -> None:
        if not (self.price > 1.0):
            raise ValueError(f"price must be > 1.0, got {self.price}")
        if self.size < 0:
            raise ValueError(f"size must be >= 0, got {self.size}")


@dataclass(frozen=True, slots=True)
class RunnerBook:
    selection_id: SelectionId
    # Best-effort top-of-book view (we can generalize to ladders later)
    best_back: PriceSize | None
    best_lay: PriceSize | None
