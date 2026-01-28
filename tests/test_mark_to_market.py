from bfrepricer.execution.position import Position
from bfrepricer.execution.mark_to_market import mark_to_market
from bfrepricer.domain.types import PriceSize


def test_long_position_marked_on_lay():
    pos = Position(size=2.0, avg_price=3.0, realized_pnl=0.0)
    mtm = mark_to_market(pos, best_back=None, best_lay=PriceSize(3.2, 10.0))
    assert round(mtm, 4) == 0.4


def test_short_position_marked_on_back():
    pos = Position(size=-2.0, avg_price=3.0, realized_pnl=0.0)
    mtm = mark_to_market(pos, best_back=PriceSize(2.8, 10.0), best_lay=None)
    assert round(mtm, 4) == 0.4


def test_no_prices_fails_closed():
    pos = Position(size=2.0, avg_price=3.0, realized_pnl=0.0)
    assert mark_to_market(pos, best_back=None, best_lay=None) == 0.0
