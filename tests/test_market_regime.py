from datetime import timedelta

import pytest

from bfrepricer.domain.events import MarketTick
from bfrepricer.domain.regime import MarketRegime
from bfrepricer.domain.types import MarketId, RunnerBook, SelectionId, utc_now
from bfrepricer.state.market_state import MarketState, UnsafeMarketRegime


def tick(mid, seq, is_open):
    return MarketTick(
        market_id=mid,
        seq=seq,
        publish_time=utc_now(),
        runners=(RunnerBook(SelectionId(1), None, None),),
        is_market_open=is_open,
    )


def test_open_allows_execution():
    mid = MarketId("1.1")
    s = MarketState(mid)
    s.apply(tick(mid, 1, True))
    assert s.can_execute() is True


def test_suspended_blocks_execution():
    mid = MarketId("1.1")
    s = MarketState(mid)
    s.apply(tick(mid, 1, True))
    s.apply(tick(mid, 2, False))
    assert s.can_execute() is False
    with pytest.raises(UnsafeMarketRegime):
        s.assert_safe_to_execute()


def test_unknown_blocks_execution():
    mid = MarketId("1.1")
    s = MarketState(mid)
    assert s.can_execute() is False
