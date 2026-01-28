from __future__ import annotations

from enum import Enum, auto


class MarketRegime(Enum):
    UNKNOWN = auto()
    OPEN = auto()
    SUSPENDED = auto()
    IN_PLAY = auto()
    CLOSED = auto()
