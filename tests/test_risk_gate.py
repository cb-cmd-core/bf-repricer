from bfrepricer.execution.risk import RiskGate, RiskConfig
from bfrepricer.execution.position import Position
from bfrepricer.execution.intent import OrderIntent, Side
from bfrepricer.domain.types import MarketId, SelectionId


def test_blocks_increasing_over_selection_cap():
    gate = RiskGate(RiskConfig(max_abs_pos_per_selection=2.0, max_abs_pos_per_market=10.0, max_order_size=5.0))
    mid = MarketId("1.1")
    sid = SelectionId(11)

    positions = {(mid, sid): Position(size=2.0, avg_price=3.0, realized_pnl=0.0)}
    intents = [OrderIntent(mid, sid, Side.BACK, price=3.0, size=2.0, reason="entry")]

    filtered = gate.filter_intents(intents=intents, positions=dict(positions))
    assert filtered == []


def test_allows_reducing_even_if_over_cap():
    gate = RiskGate(RiskConfig(max_abs_pos_per_selection=2.0, max_abs_pos_per_market=10.0, max_order_size=5.0))
    mid = MarketId("1.1")
    sid = SelectionId(11)

    positions = {(mid, sid): Position(size=5.0, avg_price=3.0, realized_pnl=0.0)}
    intents = [OrderIntent(mid, sid, Side.LAY, price=3.0, size=2.0, reason="close")]

    filtered = gate.filter_intents(intents=intents, positions=dict(positions))
    assert len(filtered) == 1
    assert filtered[0].size == 2.0


def test_clamps_order_size():
    gate = RiskGate(RiskConfig(max_abs_pos_per_selection=10.0, max_abs_pos_per_market=30.0, max_order_size=1.5))
    mid = MarketId("1.1")
    sid = SelectionId(11)

    positions = {}
    intents = [OrderIntent(mid, sid, Side.BACK, price=3.0, size=10.0, reason="entry")]

    filtered = gate.filter_intents(intents=intents, positions=dict(positions))
    assert len(filtered) == 1
    assert filtered[0].size == 1.5
