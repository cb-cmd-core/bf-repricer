from bfrepricer.execution.engine import ExecutionEngine
from bfrepricer.execution.intent import OrderIntent, Side
from bfrepricer.domain.types import MarketId, SelectionId


def test_open_and_close_position():
    eng = ExecutionEngine()
    mid = MarketId("1.1")
    sid = SelectionId(11)

    eng.process([
        OrderIntent(mid, sid, Side.BACK, price=2.0, size=2.0, reason="open"),
    ])

    snap = eng.snapshot()
    assert snap["1.1:11"]["size"] == 2.0

    eng.process([
        OrderIntent(mid, sid, Side.LAY, price=2.2, size=2.0, reason="close"),
    ])

    snap = eng.snapshot()
    assert snap["1.1:11"]["size"] == 0.0
    assert snap["1.1:11"]["realized_pnl"] > 0
