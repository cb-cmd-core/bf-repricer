from __future__ import annotations

from dataclasses import dataclass
from bfrepricer.execution.intent import Side


@dataclass
class Position:
    size: float = 0.0        # positive = long, negative = short
    avg_price: float = 0.0
    realized_pnl: float = 0.0

    def apply_fill(self, side: Side, price: float, size: float) -> None:
        signed = size if side == Side.BACK else -size

        # closing or reducing
        if self.size != 0 and (self.size > 0) != (signed > 0):
            closing = min(abs(self.size), abs(signed))
            pnl = closing * (price - self.avg_price) * (1 if self.size > 0 else -1)
            self.realized_pnl += pnl
            self.size += signed
            if self.size == 0:
                self.avg_price = 0.0
            return

        # opening or increasing
        new_size = self.size + signed
        self.avg_price = (
            (self.avg_price * self.size + price * signed) / new_size
            if self.size != 0 else price
        )
        self.size = new_size
