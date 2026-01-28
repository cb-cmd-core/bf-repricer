from bfrepricer.execution.close_rule import CloseRule, CloseRuleConfig
from bfrepricer.execution.position import Position
from bfrepricer.domain.types import MarketId, SelectionId, RunnerBook, PriceSize


def test_take_profit_closes_long():
    rule = CloseRule(CloseRuleConfig(take_profit_delta=0.1, stop_loss_delta=0.1))
    mid = MarketId("1.1")
    sel = SelectionId(11)

    positions = {(mid, sel): Position(size=2.0, avg_price=3.0, realized_pnl=0.0)}
    runners = {sel: RunnerBook(selection_id=sel, best_back=PriceSize(3.08, 10), best_lay=PriceSize(3.12, 10))}

    intents = rule.decide_closes(market_id=mid, runners=runners, positions=positions)
    assert len(intents) == 1
    assert intents[0].side.value == "LAY"
    assert intents[0].size == 2.0


def test_stop_loss_closes_long():
    rule = CloseRule(CloseRuleConfig(take_profit_delta=0.1, stop_loss_delta=0.1))
    mid = MarketId("1.1")
    sel = SelectionId(11)

    positions = {(mid, sel): Position(size=2.0, avg_price=3.0, realized_pnl=0.0)}
    runners = {sel: RunnerBook(selection_id=sel, best_back=PriceSize(2.85, 10), best_lay=PriceSize(2.88, 10))}

    intents = rule.decide_closes(market_id=mid, runners=runners, positions=positions)
    assert len(intents) == 1
    assert intents[0].side.value == "LAY"
    assert intents[0].size == 2.0


def test_take_profit_closes_short():
    rule = CloseRule(CloseRuleConfig(take_profit_delta=0.1, stop_loss_delta=0.1))
    mid = MarketId("1.1")
    sel = SelectionId(11)

    positions = {(mid, sel): Position(size=-2.0, avg_price=3.0, realized_pnl=0.0)}
    runners = {sel: RunnerBook(selection_id=sel, best_back=PriceSize(2.85, 10), best_lay=PriceSize(2.88, 10))}

    intents = rule.decide_closes(market_id=mid, runners=runners, positions=positions)
    assert len(intents) == 1
    assert intents[0].side.value == "BACK"
    assert intents[0].size == 2.0
