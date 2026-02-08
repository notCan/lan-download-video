"""
yt-dlp wrapper: download from URL with progress hooks, optional cookie file.
Queue: one worker, task state in memory (percent, eta, status).
"""
import os
import queue
import threading
import uuid
from pathlib import Path

import yt_dlp

DOWNLOADS_DIR = Path(__file__).resolve().parent / "downloads"
DOWNLOADS_DIR.mkdir(exist_ok=True)

# In-memory task state: task_id -> { status, percent, eta, filename?, error? }
_task_state: dict[str, dict] = {}
_lock = threading.Lock()
_download_queue: queue.Queue = queue.Queue()
_worker_started = False


def _set_state(task_id: str, **kwargs) -> None:
    with _lock:
        if task_id not in _task_state:
            _task_state[task_id] = {"status": "pending", "percent": 0, "eta": None, "filename": None, "error": None}
        for k, v in kwargs.items():
            _task_state[task_id][k] = v


def get_status(task_id: str) -> dict | None:
    with _lock:
        return _task_state.get(task_id)


def _progress_hook(d: dict, task_id: str) -> None:
    if d.get("status") == "downloading":
        percent = d.get("percent")
        eta = d.get("eta")
        _set_state(task_id, status="downloading", percent=percent or 0, eta=eta)
    elif d.get("status") == "finished":
        # Final filename may be in filename (post-convert)
        path = d.get("filename") or d.get("filepath")
        if path:
            _set_state(task_id, filename=os.path.basename(path))
        _set_state(task_id, status="downloading", percent=100, eta=0)


def _run_download(task_id: str, url: str, cookie_file: str | None) -> None:
    out_tmpl = str(DOWNLOADS_DIR / "%(title).100s [%(id)s].%(ext)s")
    opts = {
        "outtmpl": out_tmpl,
        "quiet": False,
        "merge_output_format": "mp4",
        "progress_hooks": [lambda d: _progress_hook(d, task_id)],
    }
    if cookie_file and os.path.isfile(cookie_file):
        opts["cookiefile"] = cookie_file
    try:
        _set_state(task_id, status="downloading", percent=0, eta=None)
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
        if info and info.get("requested_downloads"):
            # Single file
            req = info["requested_downloads"][0]
            filename = os.path.basename(req.get("filepath", ""))
        else:
            # Fallback: find newest file in downloads dir
            files = list(DOWNLOADS_DIR.iterdir())
            if files:
                newest = max(files, key=lambda p: p.stat().st_mtime)
                filename = newest.name
            else:
                filename = ""
        _set_state(task_id, status="done", percent=100, eta=0, filename=filename, error=None)
    except Exception as e:
        err_msg = str(e)
        if not err_msg:
            err_msg = "Bilinmeyen hata"
        _set_state(task_id, status="error", error=err_msg, filename=None)


def _worker() -> None:
    while True:
        item = _download_queue.get()
        if item is None:
            break
        task_id, url, cookie_file = item
        _run_download(task_id, url, cookie_file)
        _download_queue.task_done()


def _ensure_worker() -> None:
    global _worker_started
    if _worker_started:
        return
    with _lock:
        if _worker_started:
            return
        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        _worker_started = True


def enqueue_download(url: str, cookie_file: str | None = None) -> str:
    """Add download to queue. Returns task_id."""
    task_id = str(uuid.uuid4())
    _set_state(task_id, status="pending", percent=0, eta=None, filename=None, error=None)
    _ensure_worker()
    _download_queue.put((task_id, url, cookie_file))
    return task_id
