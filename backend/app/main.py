import hmac, os, re, uuid
from datetime import datetime, timezone
from fastapi import Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.auth import CurrentUser, clear_failed_logins, clear_session, csrf_protect, hash_password, login_is_blocked, normalize_username, record_failed_login, set_session, signup_request_key, verify_password, within_signup_transaction
from app.models.database import Base, Parcel, SessionLocal, User, engine
from app.models.schemas import AuthenticatedUser, CheckSavedParcelRequest, LoginRequest, OCRResponse, SaveParcelRequest, SavedParcel, SignupRequest, TrackRequest, TrackingResponse
from app.providers.apsrtc import APSRTCProvider, ProviderError
from app.services.ocr import extract_receipt

# Alembic owns PostgreSQL schema creation. This preserves lightweight SQLite setup
# for fresh local-development databases without silently changing an existing one.
if DATABASE_URL := os.getenv("DATABASE_URL", "sqlite:///./parcelpulse.db"):
    if DATABASE_URL.startswith("sqlite"): Base.metadata.create_all(bind=engine)
app = FastAPI(title="ParcelPulse", version="0.1.0")
cors_origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if origin.strip()]
app.add_middleware(CORSMiddleware, allow_origins=cors_origins, allow_credentials=True, allow_methods=["GET", "POST", "DELETE"], allow_headers=["Content-Type"])

@app.middleware("http")
async def prevent_private_api_caching(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response

def db():
    session = SessionLocal()
    try: yield session
    finally: session.close()
def serialize(p: Parcel) -> SavedParcel:
    return SavedParcel(id=p.id, tracking_number=p.tracking_number, provider=p.provider, origin=p.origin, destination=p.destination, current_status=p.current_status, events=p.events, last_successful_check=p.last_successful_check.replace(tzinfo=timezone.utc), monitoring_enabled=p.monitoring_enabled)
@app.get("/health")
def health(): return {"status": "ok", "background_monitoring": os.getenv("ENABLE_BACKGROUND_MONITORING", "false").lower() == "true"}
@app.post("/api/auth/login", response_model=AuthenticatedUser, dependencies=[Depends(csrf_protect)])
def login(payload: LoginRequest, response: Response, session: Session = Depends(db)):
    username = normalize_username(payload.username)
    if login_is_blocked(session, username): raise HTTPException(429, "Too many sign-in attempts. Please try again later.")
    user = session.query(User).filter_by(username=username).one_or_none()
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        record_failed_login(session, username)
        raise HTTPException(401, "Invalid username or password.")
    clear_failed_logins(session, username)
    set_session(response, user)
    return AuthenticatedUser(id=user.id, username=user.username)
@app.post("/api/auth/signup", response_model=AuthenticatedUser, status_code=201, dependencies=[Depends(csrf_protect)])
def signup(payload: SignupRequest, request: Request, response: Response, session: Session = Depends(db)):
    """Create an account only while a private, time-limited gate is enabled."""
    signup_key = signup_request_key(request)
    if login_is_blocked(session, signup_key, "signup"):
        raise HTTPException(429, "Too many sign-up attempts. Please try again later.")
    configured_code = os.getenv("PRIVATE_SIGNUP_CODE")
    enabled = os.getenv("SIGNUP_ENABLED", "false").lower() == "true"
    if not enabled or not configured_code or not hmac.compare_digest(payload.signup_code, configured_code):
        record_failed_login(session, signup_key, "signup")
        raise HTTPException(403, "Sign-up is currently unavailable or the code is incorrect.")
    with within_signup_transaction(session):
        # The PostgreSQL advisory lock remains held through commit, preventing
        # concurrent requests from both claiming the final available slot.
        if session.query(User).count() >= 2:
            raise HTTPException(409, "Private account capacity has been reached.")
        username = normalize_username(payload.username)
        if session.query(User).filter_by(username=username).first() is not None:
            raise HTTPException(409, "That username is unavailable.")
        user = User(username=username, password_hash=hash_password(payload.password))
        session.add(user)
        session.commit()
        session.refresh(user)
    clear_failed_logins(session, signup_key, "signup")
    set_session(response, user)
    return AuthenticatedUser(id=user.id, username=user.username)
@app.post("/api/auth/logout", status_code=204, dependencies=[Depends(csrf_protect)])
def logout(response: Response, _: CurrentUser): clear_session(response)
@app.get("/api/auth/me", response_model=AuthenticatedUser)
def me(user: CurrentUser): return AuthenticatedUser(id=user.id, username=user.username)
@app.post("/api/track", response_model=TrackingResponse, dependencies=[Depends(csrf_protect)])
async def track(payload: TrackRequest, _: CurrentUser):
    try: return await APSRTCProvider().track(payload.tracking_number, payload.mobile_number)
    except ProviderError as exc: raise HTTPException(502, str(exc))
@app.post("/api/receipts/extract", response_model=OCRResponse, dependencies=[Depends(csrf_protect)])
async def receipt(_: CurrentUser, file: UploadFile = File(...)):
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}: raise HTTPException(415, "Upload a JPEG, PNG, or WebP image.")
    data = await file.read()
    if len(data) > int(os.getenv("MAX_UPLOAD_MB", "8")) * 1024 * 1024: raise HTTPException(413, "Image is too large.")
    try: return extract_receipt(data)
    except ValueError as exc: raise HTTPException(422, str(exc))
@app.get("/api/parcels", response_model=list[SavedParcel])
def parcels(user: CurrentUser, session: Session = Depends(db)): return [serialize(p) for p in session.query(Parcel).filter_by(user_id=user.id).order_by(Parcel.last_successful_check.desc())]
@app.post("/api/parcels", response_model=SavedParcel, dependencies=[Depends(csrf_protect)])
def save(payload: SaveParcelRequest, user: CurrentUser, session: Session = Depends(db)):
    p = session.query(Parcel).filter_by(user_id=user.id, tracking_number=payload.tracking_number, provider=payload.provider).one_or_none()
    if p is None:
        p = Parcel(user_id=user.id, tracking_number=payload.tracking_number, mobile_number=payload.mobile_number, provider=payload.provider, origin=payload.origin, destination=payload.destination, current_status=payload.current_status, events=[e.model_dump() for e in payload.events], last_successful_check=datetime.now(timezone.utc), monitoring_enabled=False); session.add(p)
    else:
        p.mobile_number, p.origin, p.destination, p.current_status, p.events = payload.mobile_number, payload.origin, payload.destination, payload.current_status, [e.model_dump() for e in payload.events]
        p.monitoring_enabled, p.last_successful_check = False, datetime.now(timezone.utc)
    session.commit(); session.refresh(p); return serialize(p)
@app.post("/api/parcels/{parcel_id}/check", response_model=SavedParcel, dependencies=[Depends(csrf_protect)])
async def check_saved_parcel(parcel_id: int, payload: CheckSavedParcelRequest, user: CurrentUser, session: Session = Depends(db)):
    p = session.query(Parcel).filter_by(id=parcel_id, user_id=user.id).one_or_none()
    if not p: raise HTTPException(404, "Parcel not found.")
    mobile_number = p.mobile_number if re.fullmatch(r"\d{10}", p.mobile_number or "") else payload.mobile_number
    if not mobile_number: raise HTTPException(409, "A sender or receiver mobile number is needed to check this parcel.")
    try:
        result = await APSRTCProvider().track(p.tracking_number, mobile_number)
    except ProviderError as exc:
        raise HTTPException(502, str(exc))
    p.mobile_number = mobile_number
    p.origin, p.destination, p.current_status = result.origin, result.destination, result.current_status
    p.events = [event.model_dump() for event in result.events]
    p.last_successful_check, p.monitoring_enabled = result.last_successful_check, False
    session.commit(); session.refresh(p)
    return serialize(p)
@app.delete("/api/parcels/{parcel_id}", status_code=204, dependencies=[Depends(csrf_protect)])
def delete(parcel_id: int, user: CurrentUser, session: Session = Depends(db)):
    p = session.query(Parcel).filter_by(id=parcel_id, user_id=user.id).one_or_none()
    if not p: raise HTTPException(404, "Parcel not found.")
    session.delete(p); session.commit()
