from datetime import datetime
from bfrepricer.domain.events import MarketTick
from bfrepricer.domain.types import MarketId, SelectionId, RunnerBook

def normalize(raw: dict) -> MarketTick:
    """
    Convert a raw update from your data source into a MarketTick.
    Adapt this stub to your actual data schema.
    """
    market_id = MarketId(str(raw["market_id"]))
    seq = int(raw.get("sequence", 0))
    publish_time = raw.get("timestamp", datetime.utcnow())
    runners = tuple(
        RunnerBook(selection_id=SelectionId(int(r["selection_id"])), best_back=None, best_lay=None)
        for r in raw.get("runners", [])
    )
    return MarketTick(
        market_id=market_id,
        seq=seq,
        publish_time=publish_time,
        runners=runners,
        is_market_open=raw.get("is_market_open"),
        is_in_play=raw.get("is_in_play"),
    )
