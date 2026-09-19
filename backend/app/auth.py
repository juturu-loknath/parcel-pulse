"""Private username/password authentication for ParcelPulse.

Passwords are Argon2id hashes; browser sessions are signed, HttpOnly cookies.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, Response
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.models.database import LoginAttempt, SessionLocal, User

COOKIE_NAME = "parcelpulse_session"
PASSWORD_HASHER = PasswordHash.recommended()
SESSION_HOURS = int(os.getenv("SESSION_HOURS", "12"))
MAX_LOGIN_FAILURES = int(os.getenv("MAX_LOGIN_FAILURES", "5"))
LOGIN_WINDOW_MINUTES = int(os.getenv("LOGIN_WINDOW_MINUTES", "15"))

def auth_secret() -> str:
    secret = os.getenv("SESSION_SECRET")
    if secret: return secret
    if os.getenv("ENVIRONMENT", "development") == "production":
        raise RuntimeError("SESSION_SECRET must be configured in production.")
    return "development-only-secret-change-before-deployment"

def normalize_username(username: str) -> str:
    return username.strip().lower()

def hash_password(password: str) -> str:
    return PASSWORD_HASHER.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return PASSWORD_HASHER.verify(password, password_hash)

def _attempt_key(identifier: str, scope: str = "login") -> str:
    message = f"{scope}:{normalize_username(identifier)}"
    return hmac.new(auth_secret().encode(), message.encode(), hashlib.sha256).hexdigest()

def _utc(value: datetime | None) -> datetime | None:
    if value is None: return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

def login_is_blocked(session: Session, identifier: str, scope: str = "login") -> bool:
    attempt = session.get(LoginAttempt, _attempt_key(identifier, scope))
    return bool(attempt and (_utc(attempt.blocked_until) or datetime.min.replace(tzinfo=timezone.utc)) > datetime.now(timezone.utc))

def record_failed_login(session: Session, identifier: str, scope: str = "login") -> None:
    now, key = datetime.now(timezone.utc), _attempt_key(identifier, scope)
    attempt = session.get(LoginAttempt, key)
    if attempt is None or now - _utc(attempt.window_started_at) > timedelta(minutes=LOGIN_WINDOW_MINUTES):
        attempt = LoginAttempt(key=key, failures=0, window_started_at=now, blocked_until=None)
        session.add(attempt)
    attempt.failures += 1
    if attempt.failures >= MAX_LOGIN_FAILURES:
        attempt.blocked_until = now + timedelta(minutes=LOGIN_WINDOW_MINUTES)
    session.commit()

def clear_failed_logins(session: Session, identifier: str, scope: str = "login") -> None:
    attempt = session.get(LoginAttempt, _attempt_key(identifier, scope))
    if attempt:
        session.delete(attempt); session.commit()

def set_session(response: Response, user: User) -> None:
    now = datetime.now(timezone.utc)
    token = jwt.encode({"sub": user.id, "username": user.username, "sv": user.session_version, "iat": now, "exp": now + timedelta(hours=SESSION_HOURS)}, auth_secret(), algorithm="HS256")
    secure_cookie = os.getenv("AUTH_COOKIE_SECURE", "true" if os.getenv("ENVIRONMENT") == "production" else "false").lower() == "true"
    response.set_cookie(COOKIE_NAME, token, max_age=SESSION_HOURS * 3600, httponly=True, secure=secure_cookie, samesite="lax", path="/")

def clear_session(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")

def auth_db():
    session = SessionLocal()
    try: yield session
    finally: session.close()

def current_user(request: Request, session: Session = Depends(auth_db)) -> User:
    token = request.cookies.get(COOKIE_NAME)
    if not token: raise HTTPException(401, "Sign in is required.")
    try:
        claims = jwt.decode(token, auth_secret(), algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "Your session has expired. Please sign in again.")
    user = session.get(User, claims.get("sub"))
    if user is None or not user.is_active or claims.get("sv") != user.session_version: raise HTTPException(401, "Your session is no longer active.")
    return user

CurrentUser = Annotated[User, Depends(current_user)]

def csrf_protect(request: Request) -> None:
    """Reject cross-site browser writes while allowing trusted non-browser tooling."""
    origin = request.headers.get("origin")
    if not origin: return
    allowed = {value.strip().rstrip("/") for value in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")}
    if origin.rstrip("/") not in allowed:
        raise HTTPException(403, "This request was blocked for your security.")

def signup_request_key(request: Request) -> str:
    # Do not trust forwarded headers unless a future deployment explicitly sets
    # up trusted proxy middleware. The direct peer IP is enough for this small,
    # private signup gate.
    return request.client.host if request.client else "unknown"
