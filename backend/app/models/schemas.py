from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

class TrackRequest(BaseModel):
    tracking_number: str = Field(pattern=r"^\d{6,16}$")
    mobile_number: str = Field(pattern=r"^\d{10}$")

class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=1, max_length=256)

class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=1, max_length=256)
    signup_code: str = Field(min_length=1, max_length=256)

class AuthenticatedUser(BaseModel):
    id: str
    username: str

class TrackingEvent(BaseModel):
    status: str
    occurred_at: str | None = None
    location: str | None = None

class TrackingResponse(BaseModel):
    tracking_number: str
    provider: Literal["APSRTC"] = "APSRTC"
    origin: str | None = None
    destination: str | None = None
    current_status: str
    events: list[TrackingEvent] = []
    last_successful_check: datetime
    error: str | None = None

class OCRResponse(BaseModel):
    tracking_number: str | None = None
    sender_mobile: str | None = None
    receiver_mobile: str | None = None
    booking_date: str | None = None
    origin: str | None = None
    destination: str | None = None
    field_confidence: dict[str, str] = {}
    confidence_note: str

class SaveParcelRequest(BaseModel):
    tracking_number: str = Field(pattern=r"^\d{6,16}$")
    mobile_number: str = Field(pattern=r"^\d{10}$")
    provider: Literal["APSRTC"] = "APSRTC"
    origin: str | None = None
    destination: str | None = None
    current_status: str
    events: list[TrackingEvent] = []
    monitoring_enabled: bool = False

class CheckSavedParcelRequest(BaseModel):
    # Normally omitted: the server uses the private number stored with the parcel.
    # This is only accepted to repair legacy records that have no usable number.
    mobile_number: str | None = Field(default=None, pattern=r"^\d{10}$")

class SavedParcel(BaseModel):
    id: int
    tracking_number: str
    provider: str
    origin: str | None
    destination: str | None
    current_status: str
    events: list[TrackingEvent]
    last_successful_check: datetime
    monitoring_enabled: bool
