"""
JWT-based auth (lan-notes ile aynı): cookie "token", /api/auth/register, login, logout, me.
Kullanıcılar data/users.json içinde tutulur.
"""
import os
from datetime import datetime, timedelta
from typing import Optional

import jwt as pyjwt
from fastapi import Request, Response
from dotenv import load_dotenv

load_dotenv()

COOKIE_NAME = "token"
JWT_SECRET = os.getenv("JWT_SECRET", os.getenv("SECRET_KEY", "change-me-in-production"))
REMEMBER_ME_DAYS = 30


def create_token(user_id: str, username: str, remember_me: bool = True) -> str:
    exp_days = REMEMBER_ME_DAYS if remember_me else 1
    payload = {
        "userId": user_id,
        "username": username,
        "exp": datetime.utcnow() + timedelta(days=exp_days),
    }
    token = pyjwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token.decode() if isinstance(token, bytes) else token


def set_session_cookie(response: Response, user_id: str, username: str, remember_me: bool) -> None:
    token = create_token(user_id, username, remember_me)
    max_age = REMEMBER_ME_DAYS * 24 * 3600 if remember_me else 24 * 3600
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=True,
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=COOKIE_NAME, path="/")


def read_session(request: Request) -> Optional[dict]:
    """Read and verify JWT from cookie. Returns {id, username} or None."""
    cookie = request.cookies.get(COOKIE_NAME)
    if not cookie:
        return None
    try:
        payload = pyjwt.decode(cookie, JWT_SECRET, algorithms=["HS256"])
        uid = payload.get("userId")
        uname = payload.get("username")
        if uid and uname:
            return {"id": uid, "username": uname}
    except Exception:
        pass
    return None
