from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from bfrepricer.domain.types import MarketId, SelectionId


class Side(Enum):
    BACK = "BACK"
    LAY = "LAY"


@dataclass(frozen=True, slots=True)
class OrderIntent:
    market_id: MarketId
    selection_id: SelectionId
    side: Side
    price: float
    size: float
    reason: str


@dataclass(frozen=True, slots=True)
class IntentDecision:
    intents: Sequence[OrderIntent]
    notes: str = ""
