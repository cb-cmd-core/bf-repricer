from typing import Iterable
from bfrepricer.domain.events import MarketTick
from bfrepricer.domain.types import MarketId

class StreamingClient:
    """
    Stub for a streaming client. In production, this would wrap Betfair’s Streaming API.
    """
    def __init__(self, auth) -> None:
        self.auth = auth
        self.connected: bool = False

    def connect(self) -> None:
        """Establish a session with the streaming endpoint."""
        self.connected = True

    def subscribe_to_market(self, market_id: MarketId) -> Iterable[MarketTick]:
        """
        Yield MarketTick objects for the given market until unsubscribed.
        Not implemented here – wiring to the real data source is required.
        """
        if not self.connected:
            raise RuntimeError("Streaming client is not connected.")
        raise NotImplementedError("subscribe_to_market must be implemented by a subclass.")
