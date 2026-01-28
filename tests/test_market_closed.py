from datetime import timedelta

from bfrepricer.domain.events import MarketTick
from bfrepricer.domain.regime import MarketRegime
from bfrepricer.domain.types import MarketId, RunnerBook, SelectionId, utc_now
from bfrepricer.state.market_state import MarketState


def tick(mid, seq, *, is_open=None, in_play=None, is_closed=None, t=None, sel=1):
    return MarketTick(
        market_id=mid,
        seq=seq,
        publish_time=t or utc_now(),
        runners=(RunnerBook(SelectionId(sel), None, None),),
        is_market_open=is_open,
        is_in_play=in_play,
        is_closed=is_closed,
    )


def test_closed_is_terminal_and_blocks_execution():
    mid = MarketId("1.1")
    s = MarketState(mid, reopen_cooldown=timedelta(seconds=0))

    s.apply(tick(mid, 1, is_open=True, sel=1))
    assert s.can_execute() is True

    s.apply(tick(mid, 2, is_closed=True, sel=2))
    snap = s.snapshot()
    assert snap.regime == MarketRegime.CLOSED
    assert s.can_execute() is False

    # After CLOSED, later ticks must not mutate runners/regime
    s.apply(tick(mid, 3, is_open=True, sel=999))
    snap2 = s.snapshot()
    assert snap2.regime == MarketRegime.CLOSED
    assert SelectionId(999) not in snap2.runners
    assert SelectionId(1) in snap2.runners  # original preserved
