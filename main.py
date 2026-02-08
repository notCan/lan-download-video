"""
FastAPI app: JWT auth (lan-notes ile aynı), protected index, POST /download, GET /status, GET /downloads/<filename>.
Port 3335, host 0.0.0.0 for LAN.
"""
import json
import os
import uuid
from pathlib import Path

import bcrypt
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from auth import set_session_cookie, clear_session_cookie, read_session
from downloader import enqueue_download, get_status, DOWNLOADS_DIR

app = FastAPI(title="Video Indirici")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
STATIC_DIR = Path(__file__).resolve().parent / "static"
DATA_DIR = Path(__file__).resolve().parent / "data"
USERS_FILE = DATA_DIR / "users.json"


def ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not USERS_FILE.exists():
        USERS_FILE.write_text(json.dumps({"users": []}, indent=2), encoding="utf-8")


def read_users():
    ensure_dirs()
    return json.loads(USERS_FILE.read_text(encoding="utf-8"))


def write_users(data: dict):
    USERS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _auth_redirect(request: Request):
    """Dependency: redirect to /login if not authenticated; else return username."""
    user = read_session(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return user["username"]


@app.on_event("startup")
def startup():
    ensure_dirs()


@app.get("/manifest.json")
async def manifest():
    return FileResponse(STATIC_DIR / "manifest.json", media_type="application/json")


@app.get("/sw.js")
async def sw():
    return FileResponse(STATIC_DIR / "sw.js", media_type="application/javascript")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if read_session(request):
        return RedirectResponse(url="/", status_code=302)
    return FileResponse(STATIC_DIR / "login.html", media_type="text/html")


@app.post("/api/auth/register")
async def api_register(request: Request):
    body = await request.json()
    username = (body.get("username") or "").strip().lower()
    password = body.get("password") or ""
    if not username or not password:
        return JSONResponse({"error": "Kullanıcı adı ve şifre gerekli"}, status_code=400)
    if len(username) < 2:
        return JSONResponse({"error": "Kullanıcı adı en az 2 karakter olmalı"}, status_code=400)
    data = read_users()
    if any(u["username"] == username for u in data["users"]):
        return JSONResponse({"error": "Bu kullanıcı adı alınmış"}, status_code=400)
    user_id = str(uuid.uuid4())
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    data["users"].append({"id": user_id, "username": username, "passwordHash": password_hash})
    write_users(data)
    res = JSONResponse({"user": {"id": user_id, "username": username}}, status_code=201)
    set_session_cookie(res, user_id, username, remember_me=True)
    return res


@app.post("/api/auth/login")
async def api_login(request: Request):
    body = await request.json()
    username = (body.get("username") or "").strip().lower()
    password = body.get("password") or ""
    remember_me = bool(body.get("rememberMe", True))
    if not username or not password:
        return JSONResponse({"error": "Kullanıcı adı ve şifre gerekli"}, status_code=400)
    data = read_users()
    user = next((u for u in data["users"] if u["username"] == username), None)
    if not user or not bcrypt.checkpw(password.encode("utf-8"), user["passwordHash"].encode("utf-8")):
        return JSONResponse({"error": "Kullanıcı adı veya şifre hatalı"}, status_code=401)
    res = JSONResponse({"user": {"id": user["id"], "username": user["username"]}})
    set_session_cookie(res, user["id"], user["username"], remember_me)
    return res


@app.post("/api/auth/logout")
async def api_logout():
    res = JSONResponse(content={}, status_code=204)
    clear_session_cookie(res)
    return res


@app.get("/api/auth/me")
async def api_me(request: Request):
    user = read_session(request)
    if not user:
        return JSONResponse({"error": "Oturum açmanız gerekiyor"}, status_code=401)
    return {"user": {"id": user["id"], "username": user["username"]}}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, _: str = Depends(_auth_redirect)):
    path = STATIC_DIR / "index.html"
    return FileResponse(path, media_type="text/html")


@app.post("/download")
async def download(
    request: Request,
    _: str = Depends(_auth_redirect),
):
    body = await request.json()
    url = (body.get("url") or "").strip()
    if not url or not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Gecersiz URL.")
    cookie_file = body.get("cookie_file") or None
    if cookie_file and not os.path.isfile(cookie_file):
        cookie_file = None
    task_id = enqueue_download(url, cookie_file)
    return {"success": True, "task_id": task_id}


@app.get("/status/{task_id}")
async def status(task_id: str, _: str = Depends(_auth_redirect)):
    state = get_status(task_id)
    if not state:
        raise HTTPException(status_code=404, detail="Gorev bulunamadi.")
    return state


def _safe_filename(name: str) -> str:
    """Allow only basename, no path traversal."""
    base = os.path.basename(name)
    if not base or ".." in base or os.path.sep in base:
        return ""
    return base


@app.get("/downloads/{filename}")
async def download_file(
    filename: str,
    request: Request,
    _: str = Depends(_auth_redirect),
):
    safe = _safe_filename(filename)
    if not safe:
        raise HTTPException(status_code=400, detail="Gecersiz dosya adi.")
    path = DOWNLOADS_DIR / safe
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Dosya bulunamadi.")
    return FileResponse(path, filename=safe)


# Static assets if any (e.g. CSS) - optional
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
