from datetime import timedelta

from bfrepricer.domain.events import MarketTick
from bfrepricer.domain.regime import MarketRegime
from bfrepricer.domain.types import MarketId, RunnerBook, SelectionId, utc_now
from bfrepricer.state.market_state import MarketState


def tick(mid, seq, *, is_open=None, in_play=None, t=None):
    return MarketTick(
        market_id=mid,
        seq=seq,
        publish_time=t or utc_now(),
        runners=(RunnerBook(SelectionId(1), None, None),),
        is_market_open=is_open,
        is_in_play=in_play,
    )


def test_in_play_disables_execution_immediately_and_persistently():
    mid = MarketId("1.1")
    s = MarketState(mid, reopen_cooldown=timedelta(seconds=0))

    s.apply(tick(mid, 1, is_open=True))
    assert s.can_execute() is True

    s.apply(tick(mid, 2, in_play=True))
    assert s.can_execute() is False
    assert s.snapshot().regime == MarketRegime.IN_PLAY

    # Even if a later tick claims open, we remain IN_PLAY and blocked.
    s.apply(tick(mid, 3, is_open=True))
    assert s.snapshot().regime == MarketRegime.IN_PLAY
    assert s.can_execute() is False
