# Video İndirici (LAN)

Instagram, Twitter/X, TikTok, YouTube ve diğer 1000+ siteden video indiren, LAN'da çalışan web uygulaması. Giriş sayfası, "Beni hatırla", indirme kuyruğu ve ilerleme çubuğu içerir.

**Sürüm:** 1.0.0

---

## İlk çalıştırmadan önce eklemeniz gerekenler

| Öğe | İşlem |
|-----|--------|
| **`.env`** | `.env.example` dosyasından kopyalayın: `copy .env.example .env` (Windows) veya `cp .env.example .env` (Linux/macOS). Ardından `LOGIN_USERNAME` ve `LOGIN_PASSWORD` değerlerini ayarlayın. İsteğe bağlı: oturum çerezleri için `SECRET_KEY` (üretimde mutlaka değiştirin). |
| **FFmpeg** | [FFmpeg](https://ffmpeg.org/) kurun ve sistem PATH'ine ekleyin (bazı sitelerde video+ses birleştirme için gerekir). |
| **Python sanal ortamı** | Sanal ortam oluşturup kullanın (Kurulum bölümüne bakın). |

`downloads/` klasörünü oluşturmanız gerekmez; ilk indirmede uygulama oluşturur.

---

## Gereksinimler

- Python 3.10+
- [FFmpeg](https://ffmpeg.org/) (PATH'te olmalı; bazı siteler için video+ses birleştirme)
- İsteğe bağlı: Node.js (sadece Windows'ta `start.bat` ile QR kod için)

## Kurulum

1. Sanal ortam oluşturup bağımlılıkları yükleyin:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   # source .venv/bin/activate   # Linux/macOS
   pip install -r requirements.txt
   ```

2. `.env` dosyası oluşturun (`.env.example` kopyalayın):

   ```bash
   copy .env.example .env   # Windows
   # cp .env.example .env   # Linux/macOS
   ```

   `.env` içinde en az şunları ayarlayın:
   - `LOGIN_USERNAME` – Giriş kullanıcı adı
   - `LOGIN_PASSWORD` – Giriş şifresi
   - İsteğe bağlı: `SECRET_KEY` – Oturum çerezleri için gizli anahtar (üretimde mutlaka değiştirin)

3. FFmpeg'i sistem PATH'ine ekleyin (henüz yoksa).

## Çalıştırma

```bash
uvicorn main:app --host 0.0.0.0 --port 3369
```

- Yerel: http://127.0.0.1:3369  
- LAN: Aynı ağdaki cihazlardan `http://<bu-bilgisayarın-ip>:3369`

Windows'ta `start.bat` kullanırsanız sunucu başlar, IP ve QR kod konsola yazılır (Node.js ve `qrcode-terminal` gerekir).

## Kullanım

1. Tarayıcıda adresi açın; giriş sayfası gelir.
2. Kullanıcı adı ve şifre ile giriş yapın. "Beni hatırla" işaretlenirse oturum uzun süre (30 gün) saklanır.
3. Ana sayfada video linkini yapıştırıp "İndir"e tıklayın. İlerleme çubuğu ve bitince "Dosyayı indir" linki görünür.
4. İndirilen dosyalar proje içindeki `downloads/` klasörüne kaydedilir.

## Cookie desteği (Instagram / Twitter özel içerik)

Giriş gerektiren içerikler için yt-dlp Netscape formatında cookie dosyası kullanabilir. API'de `cookie_file` parametresi desteklenir; arayüzden dosya yükleme eklenebilir.

## Proje yapısı

- `main.py` – FastAPI uygulaması, login, indirici sayfa, `/download`, `/status`, `/downloads/<filename>`
- `auth.py` – Oturum (imzalı çerez), "Beni hatırla" süresi, şifre doğrulama
- `downloader.py` – yt-dlp sarmalayıcı, kuyruk, ilerleme durumu
- `static/login.html` – Giriş formu
- `static/index.html` – Ana sayfa (link input, sonuç kutusu, progress bar)
- `downloads/` – İndirilen videolar (`.gitignore` içinde)
