class RiskManager:
    """
    Basic risk management. Enforces maximum exposure per market.
    """
    def __init__(self, max_exposure: float) -> None:
        self.max_exposure = max_exposure

    def check_order(self, proposed_exposure: float) -> bool:
        return proposed_exposure <= self.max_exposure
