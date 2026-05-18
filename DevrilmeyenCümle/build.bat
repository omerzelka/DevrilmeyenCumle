@echo off
echo === Devrilmeyen Cumle - Build (Windows) ===

:: Sanal ortam varsa aktif et
if exist ".venv\Scripts\activate.bat" (
    echo Sanal ortam (.venv) bulundu, aktif ediliyor...
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo Sanal ortam (venv) bulundu, aktif ediliyor...
    call venv\Scripts\activate.bat
)

:: Python kontrolu
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Hata: Python kurulu degil veya PATH'e eklenmemis!
    pause
    exit /b 1
)

:: Gerekli paketler
echo Gerekli paketler kontrol ediliyor/kuruluyor...
python -m pip install pyinstaller pygame-ce

:: Build islemi
echo Derleniyor...
python -m PyInstaller CumleKurmaYarisi.spec --clean --noconfirm

echo.
echo === Build tamamlandi! ===
echo.
echo Olusturulan exe dosyasini 'dist' klasorunde bulabilirsiniz.
echo Ornek: dist\Devrilmeyen Cumle.app veya .exe
echo.
pause
