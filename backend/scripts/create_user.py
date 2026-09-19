"""Create one approved ParcelPulse account interactively on a trusted machine."""
import getpass
from app.auth import hash_password, normalize_username
from app.models.database import SessionLocal, User

username = normalize_username(input("Username: "))
password = getpass.getpass("Password: ")
confirm = getpass.getpass("Confirm password: ")
if password != confirm: raise SystemExit("Passwords did not match.")
if not password: raise SystemExit("Password cannot be empty.")
session = SessionLocal()
try:
    if session.query(User).filter_by(username=username).first(): raise SystemExit("That username already exists.")
    session.add(User(username=username, password_hash=hash_password(password)))
    session.commit()
finally:
    session.close()
