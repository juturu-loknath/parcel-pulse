"""Reset an approved account after verifying the person out of band."""
import getpass
from app.auth import hash_password, normalize_username
from app.models.database import SessionLocal, User

username = normalize_username(input("Username: "))
password = getpass.getpass("New password: ")
confirm = getpass.getpass("Confirm new password: ")
if password != confirm: raise SystemExit("Passwords did not match.")
if not password: raise SystemExit("Password cannot be empty.")
session = SessionLocal()
try:
    user = session.query(User).filter_by(username=username).one_or_none()
    if user is None: raise SystemExit("Approved account not found.")
    user.password_hash = hash_password(password)
    user.session_version += 1
    session.commit()
finally:
    session.close()
