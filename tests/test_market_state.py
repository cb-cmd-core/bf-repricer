from datetime import timedelta

import pytest

from bfrepricer.domain.events import MarketTick
from bfrepricer.domain.types import MarketId, PriceSize, RunnerBook, SelectionId, utc_now
from bfrepricer.state.market_state import MarketState, OutOfOrderTick, StaleMarketData


def mk_tick(mid: MarketId, seq: int):
    t = utc_now()
    runners = (
        RunnerBook(
            selection_id=SelectionId(11),
            best_back=PriceSize(2.0, 10.0),
            best_lay=PriceSize(2.02, 12.0),
        ),
    )
    return MarketTick(market_id=mid, seq=seq, publish_time=t, runners=runners, is_market_open=True)


def test_apply_is_idempotent_on_duplicate_seq():
    mid = MarketId("1.234")
    s = MarketState(mid)
    tick = mk_tick(mid, 1)
    s.apply(tick)
    snap1 = s.snapshot()
    s.apply(tick)  # duplicate
    snap2 = s.snapshot()
    assert snap1.last_seq == snap2.last_seq
    assert snap1.runners.keys() == snap2.runners.keys()


def test_apply_rejects_out_of_order_seq():
    mid = MarketId("1.234")
    s = MarketState(mid)
    s.apply(mk_tick(mid, 2))
    with pytest.raises(OutOfOrderTick):
        s.apply(mk_tick(mid, 1))


def test_freshness_guard_raises_before_any_ticks():
    mid = MarketId("1.234")
    s = MarketState(mid)
    with pytest.raises(StaleMarketData):
        s.assert_fresh(max_age=timedelta(seconds=2))


def test_runner_updates_merge():
    mid = MarketId("1.234")
    s = MarketState(mid)
    t1 = utc_now()
    s.apply(
        MarketTick(
            market_id=mid,
            seq=1,
            publish_time=t1,
            runners=(RunnerBook(SelectionId(11), None, None),),
            is_market_open=True,
        )
    )
    t2 = utc_now()
    s.apply(
        MarketTick(
            market_id=mid,
            seq=2,
            publish_time=t2,
            runners=(RunnerBook(SelectionId(22), None, None),),
            is_market_open=True,
        )
    )
    snap = s.snapshot()
    assert SelectionId(11) in snap.runners
    assert SelectionId(22) in snap.runners
