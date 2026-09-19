from abc import ABC, abstractmethod
from app.models.schemas import TrackingResponse

class TrackingProvider(ABC):
    @abstractmethod
    async def track(self, tracking_number: str, mobile_number: str) -> TrackingResponse: ...
