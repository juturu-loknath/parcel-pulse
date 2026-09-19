from datetime import datetime, timezone
import os
import httpx
from app.models.schemas import TrackingEvent, TrackingResponse
from app.providers.base import TrackingProvider

class ProviderError(Exception): pass

class APSRTCProvider(TrackingProvider):
    endpoint = "https://cargo.apsrtconline.in/api/customer/customer/booking/getBookingDetails"
    def __init__(self, client: httpx.AsyncClient | None = None): self.client = client
    async def track(self, tracking_number: str, mobile_number: str) -> TrackingResponse:
        timeout, retries = float(os.getenv("APSRTC_TIMEOUT_SECONDS", "12")), int(os.getenv("APSRTC_MAX_RETRIES", "1"))
        own_client = self.client is None
        client = self.client or httpx.AsyncClient(timeout=timeout)
        try:
            last_error = None
            for _ in range(retries + 1):
                try:
                    # APSRTC accepts either party's number, but the unused field must be blank.
                    # Try receiver first because that is the common ParcelPulse workflow.
                    for payload in (
                        {"id": tracking_number, "fromMobile": "", "toMobile": mobile_number},
                        {"id": tracking_number, "fromMobile": mobile_number, "toMobile": ""},
                    ):
                        response = await client.post(self.endpoint, json=payload, headers={"Accept": "application/json", "Content-Type": "application/json"})
                        if response.status_code != 200: raise ProviderError("The tracking service is temporarily unavailable.")
                        data = response.json()
                        if not isinstance(data, dict): raise ProviderError("The tracking service returned an incomplete response.")
                        if data.get("error") is True: continue
                        status = data.get("currentStatus")
                        if not isinstance(status, str) or not status.strip(): raise ProviderError("The tracking service returned an incomplete response.")
                        events = [TrackingEvent(status=str(e.get("statusStr", "Update")), occurred_at=e.get("dateTime"), location=e.get("placeName")) for e in data.get("serviceStatusList", []) if isinstance(e, dict)]
                        return TrackingResponse(tracking_number=tracking_number, origin=data.get("fromPlaceName"), destination=data.get("toPlaceName"), current_status=status, events=events, last_successful_check=datetime.now(timezone.utc))
                    raise ProviderError("No parcel was found with those details.")
                except (httpx.TimeoutException, httpx.NetworkError, ValueError) as exc: last_error = exc
            raise ProviderError("Could not reach the tracking service. Please try again later.") from last_error
        finally:
            if own_client: await client.aclose()
