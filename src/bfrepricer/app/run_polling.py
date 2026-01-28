from __future__ import annotations

import os
import time

from bfrepricer.ingest.betfair_adapter import market_tick_from_book
from bfrepricer.ingest.betfair_rest import BetfairClient
from bfrepricer.pricing.strategy import StrategyConfig, TopOfBookMicroStrategy
from bfrepricer.execution.engine import ExecutionEngine
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
        if not state or not state.can_execute():
            print(f"[{tick.seq}] guard blocked (regime/cooldown)")
            time.sleep(2)
            continue

        decision = strat.decide(state.snapshot())
        exec_engine.process(decision.intents)

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
