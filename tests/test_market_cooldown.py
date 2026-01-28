from datetime import timedelta

import pytest

from bfrepricer.domain.events import MarketTick
from bfrepricer.domain.types import MarketId, RunnerBook, SelectionId, utc_now
from bfrepricer.state.market_state import MarketState, UnsafeMarketRegime


def tick(mid, seq, is_open, t):
    return MarketTick(
        market_id=mid,
        seq=seq,
        publish_time=t,
        runners=(RunnerBook(SelectionId(1), None, None),),
        is_market_open=is_open,
    )


def test_reopen_applies_cooldown_then_allows():
    mid = MarketId("1.1")
    cooldown = timedelta(seconds=5)
    s = MarketState(mid, reopen_cooldown=cooldown)

    t0 = utc_now()
    s.apply(tick(mid, 1, False, t0))  # suspended

    t1 = t0 + timedelta(seconds=1)
    s.apply(tick(mid, 2, True, t1))   # reopen

    assert s.can_execute(now=t1) is False
    with pytest.raises(UnsafeMarketRegime):
        s.assert_safe_to_execute(now=t1)

    t_ok = t1 + cooldown
    assert s.can_execute(now=t_ok) is True


def test_open_from_unknown_is_fail_closed_until_cooldown():
    mid = MarketId("1.1")
    cooldown = timedelta(seconds=3)
    s = MarketState(mid, reopen_cooldown=cooldown)

    t0 = utc_now()
    s.apply(tick(mid, 1, True, t0))

    assert s.can_execute(now=t0) is False
    assert s.can_execute(now=t0 + cooldown) is True
