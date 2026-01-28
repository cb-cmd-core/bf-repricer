from typing import Dict
from bfrepricer.state.market_state import MarketSnapshot

class BasePricingModel:
    """
    Base class for pricing logic. Subclasses should override `price_market` to return
    a mapping of selection_id -> fair price (float).
    """
    def price_market(self, snapshot: MarketSnapshot) -> Dict[int, float]:
        raise NotImplementedError

class IdentityPricingModel(BasePricingModel):
    """
    Example model: returns the top-of-book lay price as the 'fair' price.
    """
    def price_market(self, snapshot: MarketSnapshot) -> Dict[int, float]:
        return {
            runner.selection_id: (runner.best_lay.price if runner.best_lay else None)
            for runner in snapshot.runners.values()
        }
