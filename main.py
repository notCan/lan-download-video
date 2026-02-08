"""
FastAPI app: login, protected index, POST /download (queue), GET /status, GET /downloads/<filename>.
Port 3369, host 0.0.0.0 for LAN.
"""
import os
from pathlib import Path

from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from auth import (
    verify_password,
    set_session_cookie,
    clear_session_cookie,
    read_session,
)
from downloader import enqueue_download, get_status, DOWNLOADS_DIR

app = FastAPI(title="Video Indirici")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
STATIC_DIR = Path(__file__).resolve().parent / "static"


def _auth_redirect(request: Request):
    """Dependency: redirect to /login if not authenticated; else return username."""
    username = read_session(request)
    if not username:
        return RedirectResponse(url="/login", status_code=302)
    return username


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if read_session(request):
        return RedirectResponse(url="/", status_code=302)
    path = STATIC_DIR / "login.html"
    return FileResponse(path, media_type="text/html")


@app.post("/login")
async def login(
    username: str = Form(...),
    password: str = Form(...),
    remember_me: str = Form(""),
):
    try:
        remember = remember_me.strip().lower() in ("on", "1", "true", "yes")
        if verify_password(username, password):
            res = RedirectResponse(url="/", status_code=302)
            set_session_cookie(res, username, remember)
            return res
    except Exception as e:
        path = STATIC_DIR / "login.html"
        html = path.read_text(encoding="utf-8")
        err = '<p class="error">Giriş hatası. .env dosyasında LOGIN_USERNAME ve LOGIN_PASSWORD tanımlı mı?</p>'
        if "<!-- error -->" in html:
            html = html.replace("<!-- error -->", err)
        else:
            html = html.replace("</form>", err + "\n</form>")
        return HTMLResponse(html, status_code=500)
    path = STATIC_DIR / "login.html"
    html = path.read_text(encoding="utf-8")
    err = '<p class="error">Kullanıcı adı veya şifre hatalı.</p>'
    if "<!-- error -->" in html:
        html = html.replace("<!-- error -->", err)
    else:
        html = html.replace("</form>", err + "\n</form>")
    return HTMLResponse(html, status_code=401)


@app.get("/logout")
@app.post("/logout")
async def logout():
    res = RedirectResponse(url="/login", status_code=302)
    clear_session_cookie(res)
    return res


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
