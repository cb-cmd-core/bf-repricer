from bfrepricer.domain.events import MarketTick
from bfrepricer.domain.regime import MarketRegime
from bfrepricer.domain.types import MarketId, RunnerBook, SelectionId, utc_now
from bfrepricer.state.orchestrator import MarketOrchestrator


def tick(mid, seq, *, is_open=None, in_play=None, is_closed=None):
    return MarketTick(
        market_id=mid,
        seq=seq,
        publish_time=utc_now(),
        runners=(RunnerBook(SelectionId(1), None, None),),
        is_market_open=is_open,
        is_in_play=in_play,
        is_closed=is_closed,
    )


def test_market_created_lazily():
    orch = MarketOrchestrator()
    mid = MarketId("1.1")

    assert list(orch.active_market_ids()) == []

    orch.apply(tick(mid, 1, is_open=True))
    assert list(orch.active_market_ids()) == [mid]


def test_market_evicted_on_close():
    orch = MarketOrchestrator()
    mid = MarketId("1.1")

    orch.apply(tick(mid, 1, is_open=True))
    closed = orch.apply(tick(mid, 2, is_closed=True))

    assert closed is not None
    assert closed.market_id == mid
    assert closed.snapshot.regime == MarketRegime.CLOSED

    # Market should be gone
    assert list(orch.active_market_ids()) == []


def test_no_zombie_mutation_after_close():
    orch = MarketOrchestrator()
    mid = MarketId("1.1")

    orch.apply(tick(mid, 1, is_open=True))
    orch.apply(tick(mid, 2, is_closed=True))

    # Late garbage tick should recreate a *new* state, not mutate old one
    orch.apply(tick(mid, 3, is_open=True))
    state = orch.get(mid)
    assert state is not None
    assert state.snapshot().regime != MarketRegime.CLOSED
