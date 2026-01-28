from __future__ import annotations

from datetime import timedelta

from bfrepricer.domain.events import MarketTick
from bfrepricer.domain.types import MarketId, PriceSize, RunnerBook, SelectionId, utc_now
from bfrepricer.pricing.strategy import StrategyConfig, TopOfBookMicroStrategy
from bfrepricer.state.orchestrator import MarketOrchestrator


def mk_tick(
    mid: MarketId,
    seq: int,
    *,
    is_open: bool | None = None,
    in_play: bool | None = None,
    is_closed: bool | None = None,
    back: tuple[float, float] | None = None,
    lay: tuple[float, float] | None = None,
) -> MarketTick:
    rb = RunnerBook(
        selection_id=SelectionId(11),
        best_back=PriceSize(*back) if back else None,
        best_lay=PriceSize(*lay) if lay else None,
    )
    return MarketTick(
        market_id=mid,
        seq=seq,
        publish_time=utc_now(),
        runners=(rb,),
        is_market_open=is_open,
        is_in_play=in_play,
        is_closed=is_closed,
    )


def main() -> None:
    orch = MarketOrchestrator()
    strat = TopOfBookMicroStrategy(
        StrategyConfig(
            min_size=2.0,
            max_spread_ticks=0.10,
            stake_size=2.0,
        )
    )

    mid = MarketId("1.1")

    ticks = [
        mk_tick(mid, 1, is_open=True, back=(2.00, 10.0), lay=(2.02, 12.0)),   # OPEN (cooldown will apply if UNKNOWN->OPEN)
        mk_tick(mid, 2, is_open=False, back=(2.00, 10.0), lay=(2.02, 12.0)),  # SUSPENDED
        mk_tick(mid, 3, is_open=True, back=(2.00, 10.0), lay=(2.02, 12.0)),   # REOPEN (cooldown applies)
        mk_tick(mid, 4, is_open=True, back=(2.00, 10.0), lay=(2.02, 12.0)),   # still OPEN
        mk_tick(mid, 5, in_play=True, back=(2.00, 10.0), lay=(2.02, 12.0)),   # IN_PLAY lockout
        mk_tick(mid, 6, is_closed=True, back=(2.00, 10.0), lay=(2.02, 12.0)), # CLOSED terminal
    ]

    print("paper runner: starting")
    for t in ticks:
        if t.seq == 4:
            import time
            time.sleep(3)
        if t.seq == 4:
            import time
            time.sleep(3)
        closed = orch.apply(t)
        state = orch.get(t.market_id)

        if closed is not None:
            print(f"[{t.seq}] CLOSED -> evicted market={closed.market_id} regime={closed.snapshot.regime}")
            continue

        if state is None:
            print(f"[{t.seq}] state missing (unexpected)")
            continue

        snap = state.snapshot()
        # For paper runner, we override time to allow cooldown demonstration by manually advancing
        # but since utc_now() moves, we just check and report.
        if not state.can_execute():
            print(f"[{t.seq}] regime={snap.regime.name} cooldown_until={snap.cooldown_until} -> NO EXEC (guard)")
            continue

        decision = strat.decide(snap)
        if not decision.intents:
            print(f"[{t.seq}] regime={snap.regime.name} -> NO INTENT ({decision.notes})")
            continue

        for intent in decision.intents:
            print(
                f"[{t.seq}] INTENT {intent.side.value} sel={intent.selection_id} "
                f"price={intent.price} size={intent.size} reason='{intent.reason}'"
            )

    print("paper runner: done")


if __name__ == "__main__":
    main()
