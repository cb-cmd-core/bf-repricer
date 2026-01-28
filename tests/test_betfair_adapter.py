from bfrepricer.ingest.betfair_adapter import market_tick_from_book


def test_open_market_extracts_best_prices():
    book = {
        "marketId": "1.234",
        "status": "OPEN",
        "inplay": False,
        "runners": [
            {
                "selectionId": 11,
                "ex": {
                    "availableToBack": [{"price": 2.0, "size": 10.0}],
                    "availableToLay": [{"price": 2.02, "size": 12.0}],
                },
            }
        ],
    }

    tick = market_tick_from_book(book, seq=1)
    assert tick.market_id == "1.234"
    assert tick.is_market_open is True
    assert tick.is_in_play is None
    assert tick.is_closed is None
    assert len(tick.runners) == 1
    rb = tick.runners[0]
    assert rb.selection_id == 11
    assert rb.best_back.price == 2.0
    assert rb.best_lay.price == 2.02


def test_suspended_maps_to_not_open():
    book = {"marketId": "1.234", "status": "SUSPENDED", "runners": []}
    tick = market_tick_from_book(book, seq=2)
    assert tick.is_market_open is False
    assert tick.is_closed is None


def test_closed_sets_is_closed():
    book = {"marketId": "1.234", "status": "CLOSED", "runners": []}
    tick = market_tick_from_book(book, seq=3)
    assert tick.is_closed is True


def test_inplay_true_maps_to_is_in_play():
    book = {"marketId": "1.234", "status": "OPEN", "inplay": True, "runners": []}
    tick = market_tick_from_book(book, seq=4)
    assert tick.is_in_play is True
