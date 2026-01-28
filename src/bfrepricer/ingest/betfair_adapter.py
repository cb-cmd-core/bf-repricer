from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from bfrepricer.domain.events import MarketTick
from bfrepricer.domain.types import MarketId, PriceSize, RunnerBook, SelectionId


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def best_prices_from_ex(ex: dict[str, Any]) -> tuple[PriceSize | None, PriceSize | None]:
    """
    Extract best back/lay from Betfair 'ex' structure.

    Expected keys:
      ex.availableToBack: [{price, size}, ...]
      ex.availableToLay:  [{price, size}, ...]
    """
    atb = ex.get("availableToBack") or []
    atl = ex.get("availableToLay") or []

    best_back = None
    if atb:
        bb = atb[0]
        best_back = PriceSize(float(bb["price"]), float(bb["size"]))

    best_lay = None
    if atl:
        bl = atl[0]
        best_lay = PriceSize(float(bl["price"]), float(bl["size"]))

    return best_back, best_lay


def market_tick_from_book(book: dict[str, Any], *, seq: int, publish_time: datetime | None = None) -> MarketTick:
    """
    Convert a Betfair MarketBook-like dict into our canonical MarketTick.

    Works for REST listMarketBook responses and for streaming snapshots
    as long as the structure is similar.

    Minimal expected keys on book:
      - marketId: str
      - status: "OPEN" | "SUSPENDED" | "CLOSED" | ...
      - inplay: bool (optional)
      - runners: [{selectionId: int, ex: {...}}, ...]

    We intentionally fail closed:
      - unknown status => is_market_open=None, is_closed=None
    """
    market_id = MarketId(str(book["marketId"]))
    status = book.get("status")
    in_play = book.get("inplay")

    is_market_open: bool | None = None
    is_closed: bool | None = None

    if status == "OPEN":
        is_market_open = True
    elif status == "SUSPENDED":
        is_market_open = False
    elif status == "CLOSED":
        is_closed = True
        is_market_open = False

    is_in_play: bool | None = True if in_play is True else None

    runners_raw = book.get("runners") or []
    runners: list[RunnerBook] = []
    for r in runners_raw:
        sel = SelectionId(int(r["selectionId"]))
        ex = r.get("ex") or {}
        best_back, best_lay = best_prices_from_ex(ex)
        runners.append(RunnerBook(selection_id=sel, best_back=best_back, best_lay=best_lay))

    return MarketTick(
        market_id=market_id,
        seq=seq,
        publish_time=publish_time or _utc_now(),
        runners=tuple(runners),
        is_market_open=is_market_open,
        is_in_play=is_in_play,
        is_closed=is_closed,
    )
