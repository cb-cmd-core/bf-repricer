from datetime import timedelta, timezone, datetime

from bfrepricer.domain.regime import MarketRegime
from bfrepricer.domain.types import MarketId, SelectionId, PriceSize, RunnerBook
from bfrepricer.execution.intent import Side
from bfrepricer.pricing.strategy import TopOfBookMicroStrategy, StrategyConfig
from bfrepricer.state.market_state import MarketSnapshot


def snapshot_with_runner(back_p, back_s, lay_p, lay_s):
    mid = MarketId("1.1")
    runners = {
        SelectionId(11): RunnerBook(
            selection_id=SelectionId(11),
            best_back=PriceSize(back_p, back_s) if back_p else None,
            best_lay=PriceSize(lay_p, lay_s) if lay_p else None,
        )
    }
    return MarketSnapshot(
        market_id=mid,
        last_seq=1,
        last_publish_time=datetime.now(timezone.utc),
        regime=MarketRegime.OPEN,
        cooldown_until=None,
        runners=runners,
    )


def test_emits_intent_when_book_is_sane():
    snap = snapshot_with_runner(2.0, 10.0, 2.02, 12.0)
    strat = TopOfBookMicroStrategy(StrategyConfig(min_size=2.0, max_spread_ticks=0.10, stake_size=2.0))
    decision = strat.decide(snap)
    assert len(decision.intents) == 1
    intent = decision.intents[0]
    assert intent.selection_id == SelectionId(11)
    assert intent.side == Side.BACK
    assert intent.price == 2.0
    assert intent.size == 2.0


def test_no_intent_when_spread_too_wide():
    snap = snapshot_with_runner(2.0, 10.0, 2.5, 12.0)
    strat = TopOfBookMicroStrategy(StrategyConfig(max_spread_ticks=0.10))
    decision = strat.decide(snap)
    assert len(decision.intents) == 0


def test_no_intent_when_sizes_too_small():
    snap = snapshot_with_runner(2.0, 1.0, 2.02, 1.5)
    strat = TopOfBookMicroStrategy(StrategyConfig(min_size=2.0))
    decision = strat.decide(snap)
    assert len(decision.intents) == 0
