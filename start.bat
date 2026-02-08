@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title Video İndirici (CTRL+C ile kapat)

cd /d "%~dp0"

echo.
echo ================================
echo   Video İndirici başlatılıyor
echo ================================
echo.

echo IP adresi bulunuyor...
echo.

set IP=

for /f "tokens=2 delims=:" %%A in ('ipconfig ^| findstr "IPv4"') do (
    if not defined IP (
        set IP=%%A
    )
)

set IP=!IP: =!

set QR_URL=http://!IP!:3369

echo ================================
echo   Tarayıcıda veya telefonda gir:
echo   http://!IP!:3369
echo ================================
echo.
echo QR KOD (telefonla okut):
echo.

where node >nul 2>&1
if %ERRORLEVEL% equ 0 (
    if not exist "node_modules\qrcode-terminal" (
        echo qrcode-terminal yükleniyor...
        call npm install
    )
    node -e "require('qrcode-terminal').generate('%QR_URL%', { small: true });"
) else (
    echo Node.js bulunamadı - QR atlandı. Yukarıdaki adresi kullanın.
)

echo.
echo ================================
echo   Sunucu çalışıyor...
echo   Kapatmak için CTRL + C
echo ================================
echo.

if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

set PYTHON_CMD=python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    where py >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        set PYTHON_CMD=py -3
    ) else (
        echo Python bulunamadı. Python 3 kurun veya PATH'e ekleyin.
        pause
        exit /b 1
    )
)

%PYTHON_CMD% -m uvicorn main:app --host 0.0.0.0 --port 3369

echo.
echo ================================
echo   Sunucu durduruldu
echo   Pencereyi kapatmak için bir tuşa basın
echo ================================
pause
