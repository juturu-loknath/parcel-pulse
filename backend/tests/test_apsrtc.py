from datetime import datetime
import json
import httpx
import pytest
from app.providers.apsrtc import APSRTCProvider, ProviderError

@pytest.mark.asyncio
async def test_normalizes_successful_apsrtc_response():
    payload={"error":False,"fromPlaceName":"HYDERABAD MGBS","toPlaceName":"PULIVENDULA","currentStatus":"BOOKED","serviceStatusList":[{"statusStr":"BOOKED","dateTime":"18/09/2026 21:41:56","placeName":"HYDERABAD MGBS"}]}
    requests=[]
    def handler(request):
        requests.append(request)
        return httpx.Response(200,json=payload)
    transport=httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        result=await APSRTCProvider(client).track("81174953","9000000000")
    assert result.current_status == "BOOKED"
    assert result.origin == "HYDERABAD MGBS"
    assert result.events[0].location == "HYDERABAD MGBS"
    assert json.loads(requests[0].content) == {"id": "81174953", "fromMobile": "", "toMobile": "9000000000"}

@pytest.mark.asyncio
async def test_rejects_upstream_not_found():
    transport=httpx.MockTransport(lambda request:httpx.Response(200,json={"error":True}))
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(ProviderError, match="No parcel"):
            await APSRTCProvider(client).track("81174953","9000000000")

@pytest.mark.asyncio
async def test_turns_an_upstream_timeout_into_a_safe_retry_message(monkeypatch):
    monkeypatch.setenv("APSRTC_MAX_RETRIES", "0")
    def handler(request):
        raise httpx.ReadTimeout("timed out", request=request)
    transport=httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(ProviderError, match="Could not reach"):
            await APSRTCProvider(client).track("12345678", "9123456789")
