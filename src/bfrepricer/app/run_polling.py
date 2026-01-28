from __future__ import annotations

import os
import time

from bfrepricer.ingest.betfair_adapter import market_tick_from_book
from bfrepricer.ingest.betfair_rest import BetfairClient
from bfrepricer.pricing.strategy import StrategyConfig, TopOfBookMicroStrategy
from bfrepricer.execution.engine import ExecutionEngine
from bfrepricer.execution.close_rule import CloseRule, CloseRuleConfig
from bfrepricer.execution.risk import RiskGate, RiskConfig
from bfrepricer.execution.mark_to_market import mark_to_market
from bfrepricer.state.orchestrator import MarketOrchestrator


def main() -> None:
    app_key = os.environ["BETFAIR_APP_KEY"]
    session = os.environ["BETFAIR_SESSION_TOKEN"]

    bf = BetfairClient(app_key, session)

    print("polling runner: discovering market")

    # UK / GB WIN horse racing today
    cats = bf.list_market_catalogue(
        filter={
            "eventTypeIds": ["7"],  # Horse Racing
            "marketTypeCodes": ["WIN"],
            "marketCountries": ["GB"],
            "inPlayOnly": False,
        },
        max_results=1,
    )

    if not cats:
        raise RuntimeError("No markets found")

    market_id = cats[0]["marketId"]
    print(f"polling runner: market_id={market_id}")

    orch = MarketOrchestrator()
    strat = TopOfBookMicroStrategy(StrategyConfig())
    exec_engine = ExecutionEngine()
    close_rule = CloseRule(CloseRuleConfig(take_profit_delta=0.10, stop_loss_delta=0.10))
    risk = RiskGate(RiskConfig(max_abs_pos_per_selection=10.0, max_abs_pos_per_market=30.0, max_order_size=2.0))
    loops = 0
    HEARTBEAT_EVERY = 10
    last_exec_snapshot = None

    seq = 1
    last_sig_by_market = {}
    while True:
        books = bf.list_market_book(market_id)
        if not books:
            time.sleep(2)
            continue

        tick = market_tick_from_book(books[0], seq=seq)
        seq += 1

        closed = orch.apply(tick)
        if closed:
            print(f"CLOSED -> evicted {closed.market_id}")
            break

        state = orch.get(tick.market_id)
        if not state:
            continue

        loops += 1
        if loops % HEARTBEAT_EVERY == 0:
            snap = state.snapshot()
            print(
                f"[{tick.seq}] HEARTBEAT regime={snap.regime.name} "
                f"in_play={snap.regime.name == 'IN_PLAY'} "
                f"can_execute={state.can_execute()}"
            )

        if not state.can_execute():
            print(f"[{tick.seq}] guard blocked (regime/cooldown)")
            time.sleep(2)
            continue

        decision = strat.decide(state.snapshot())
        snap = state.snapshot()
        close_intents = close_rule.decide_closes(
            market_id=tick.market_id,
            runners=snap.runners,
            positions=exec_engine.positions,
        )
        if close_intents:
            close_intents = risk.filter_intents(intents=close_intents, positions=dict(exec_engine.positions))
            exec_engine.process(close_intents)
            print(f"[{tick.seq}] CLOSE {[(i.side.value, i.selection_id, i.price, i.size, i.reason) for i in close_intents]}")
            time.sleep(2)
            continue

        # Suppress entry if we already have a position on that selection
        filtered = []
        for i in decision.intents:
            pos = exec_engine.positions.get((i.market_id, i.selection_id))
            if pos and pos.size != 0:
                continue
            filtered.append(i)
        decision = decision.__class__(intents=tuple(filtered), notes=decision.notes)
        filtered_intents = risk.filter_intents(intents=decision.intents, positions=dict(exec_engine.positions))
        decision = decision.__class__(intents=tuple(filtered_intents), notes=decision.notes)
        exec_engine.process(decision.intents)
        loops += 1
        # REPORT: only print when positions snapshot changes AND a fill happened
        if decision.intents:
            snap_exec = exec_engine.snapshot()
            if snap_exec != last_exec_snapshot:
                last_exec_snapshot = snap_exec
                # Enrich with mark-to-market PnL
                enriched = {}
                for (m, s_id), pos in exec_engine.positions.items():
                    rb = state.snapshot().runners.get(s_id)
                    mtm = mark_to_market(pos, best_back=rb.best_back if rb else None, best_lay=rb.best_lay if rb else None)
                    enriched[f"{m}:{s_id}"] = {
                        **snap_exec[f"{m}:{s_id}"],
                        "unrealized_pnl": round(mtm, 4),
                        "total_pnl": round(pos.realized_pnl + mtm, 4),
                    }
                print(f"[{tick.seq}] POSITIONS {enriched}")

        # DEDUPE: only emit if intents changed for this market
        sig = tuple(
            (i.selection_id, i.side.value, round(i.price, 4), round(i.size, 4), i.reason)
            for i in decision.intents
        )
        last_sig = last_sig_by_market.get(tick.market_id)

        if sig != last_sig:
            last_sig_by_market[tick.market_id] = sig
            if not sig:
                print(f"[{tick.seq}] NO INTENT ({decision.notes})")
            else:
                for intent in decision.intents:
                    print(
                        f"[{tick.seq}] INTENT {intent.side.value} "
                        f"sel={intent.selection_id} "
                        f"price={intent.price} size={intent.size} "
                        f"reason='{intent.reason}'"
                    )

        time.sleep(2)


if __name__ == "__main__":
    main()
