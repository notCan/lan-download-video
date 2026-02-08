# LAN Video Downloader

Download videos from Instagram, Twitter/X, TikTok, YouTube and 1000+ sites via a LAN web app. Includes login page, "Remember me", download queue and progress bar.

**Version:** 1.0.0

---

## What you need to add (before first run)

| Item | Action |
|------|--------|
| **`.env`** | Copy from `.env.example`: `copy .env.example .env` (Windows) or `cp .env.example .env` (Linux/macOS). Then set `LOGIN_USERNAME` and `LOGIN_PASSWORD`. Optionally set `SECRET_KEY` for session cookies (change in production). |
| **FFmpeg** | Install [FFmpeg](https://ffmpeg.org/) and add it to your system PATH (needed for some sites to merge video+audio). |
| **Python venv** | Create and use a virtual environment (see Setup below). |

No need to create the `downloads/` folder; the app creates it when the first download runs.

---

## Requirements

- Python 3.10+
- [FFmpeg](https://ffmpeg.org/) on PATH (for video+audio merge on some sites)
- Optional: Node.js (only for QR code in `start.bat` on Windows)

## Setup

1. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   .venv\activate        # Windows
   # source .venv/bin/activate   # Linux/macOS
   pip install -r requirements.txt
   ```

2. Create `.env` from the example and edit it:

   ```bash
   copy .env.example .env   # Windows
   # cp .env.example .env   # Linux/macOS
   ```

   Set at least:
   - `LOGIN_USERNAME` – login username
   - `LOGIN_PASSWORD` – login password
   - Optional: `SECRET_KEY` – secret for session cookies (change in production)

3. Add FFmpeg to your system PATH if not already.

## Run

```bash
uvicorn main:app --host 0.0.0.0 --port 3335
```

- Local: http://127.0.0.1:3335  
- LAN: from other devices use `http://<this-computer-ip>:3335`

On Windows you can use `start.bat`; it starts the server and shows the IP and a QR code (requires Node.js and `qrcode-terminal`).

## Usage

1. Open the URL in a browser; the login page appears.
2. Log in with your username and password. If "Remember me" is checked, the session is kept for a long time (e.g. 30 days).
3. On the main page paste a video URL and click "İndir" (Download). A progress bar and then a "Download file" link appear when done.
4. Downloaded files are saved in the project `downloads/` folder.

## Cookie support (Instagram / Twitter)

For login-required content, yt-dlp can use a Netscape-format cookie file. The API supports a `cookie_file` parameter; the UI can be extended to allow uploading it.

## Project structure

- `main.py` – FastAPI app, login, download page, `/download`, `/status`, `/downloads/<filename>`
- `auth.py` – Session (signed cookie), "Remember me" duration, password check
- `downloader.py` – yt-dlp wrapper, queue, progress status
- `static/login.html` – Login form
- `static/index.html` – Main page (URL input, result area, progress bar)
- `downloads/` – Downloaded videos (in `.gitignore`)
