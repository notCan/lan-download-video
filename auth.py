"""
Session auth: signed cookie, remember_me (long-lived vs session cookie).
Credentials from env: LOGIN_USERNAME, LOGIN_PASSWORD.
"""
import os
from typing import Optional

import bcrypt as bcrypt_lib

from fastapi import Depends, Response, Request, HTTPException
from fastapi.responses import RedirectResponse
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from dotenv import load_dotenv

load_dotenv()

COOKIE_NAME = "session"
# Use a secret from env or fallback (change in production)
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
REMEMBER_ME_DAYS = 30
# Serializer for signed session cookie
serializer = URLSafeTimedSerializer(SECRET_KEY)


def get_credentials() -> tuple[str, str]:
    username = os.getenv("LOGIN_USERNAME", "admin")
    password = os.getenv("LOGIN_PASSWORD", "")
    return username, password


def _get_stored_password_hash() -> Optional[bytes]:
    """Hash the env password once at startup for comparison."""
    _, pwd = get_credentials()
    if not pwd:
        return None
    return bcrypt_lib.hashpw(pwd.encode("utf-8"), bcrypt_lib.gensalt())


_stored_hash: Optional[bytes] = None


def _stored_pwd_hash() -> Optional[bytes]:
    global _stored_hash
    if _stored_hash is None:
        _stored_hash = _get_stored_password_hash()
    return _stored_hash


def verify_password(username: str, password: str) -> bool:
    u, _ = get_credentials()
    if u != username:
        return False
    if not password:
        return False
    stored = _stored_pwd_hash()
    if not stored:
        return False
    try:
        return bcrypt_lib.checkpw(password.encode("utf-8"), stored)
    except Exception:
        return False


def create_session_cookie(value: str, remember_me: bool) -> str:
    """Build signed cookie value. remember_me=True -> long max_age."""
    return serializer.dumps(value)


def set_session_cookie(response: Response, username: str, remember_me: bool) -> None:
    payload = username
    cookie_value = create_session_cookie(payload, remember_me)
    max_age = REMEMBER_ME_DAYS * 24 * 3600 if remember_me else None
    response.set_cookie(
        key=COOKIE_NAME,
        value=cookie_value,
        max_age=max_age,
        httponly=True,
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=COOKIE_NAME, path="/")


def read_session(request: Request) -> Optional[str]:
    """Read and verify session cookie. Returns username or None."""
    cookie = request.cookies.get(COOKIE_NAME)
    if not cookie:
        return None
    try:
        # For session cookie (no max_age) we use max_age for verification window
        payload = serializer.loads(cookie, max_age=REMEMBER_ME_DAYS * 24 * 3600)
        return payload
    except (BadSignature, SignatureExpired, Exception):
        return None


def require_auth(request: Request) -> str:
    """Dependency: raises 302 to /login if not authenticated. Returns username."""
    username = read_session(request)
    if not username:
        raise HTTPException(status_code=302, detail="Login required", headers={"Location": "/login"})
    return username


def require_auth_redirect(request: Request):
    """Dependency that returns RedirectResponse to /login if not authenticated."""
    username = read_session(request)
    if not username:
        return RedirectResponse(url="/login", status_code=302)
    return username
