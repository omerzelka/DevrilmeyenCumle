#!/bin/bash
# Mac ve Windows icin exe/app olusturma scripti
# Kullanim: bash build.sh

echo "=== Devrilmeyen Cümle - Build (Mac/Linux) ==="

# Sanal ortam varsa aktif et
if [ -d ".venv" ]; then
    echo "Sanal ortam (.venv) bulundu, aktif ediliyor..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "Sanal ortam (venv) bulundu, aktif ediliyor..."
    source venv/bin/activate
fi

# 1. Sistemdeki gecerli Python komutunu bul (Mac icin python3, Windows icin python)
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "Hata: Python kurulu degil veya PATH'e eklenmemis!"
    exit 1
fi

echo "Kullanilan Python surumu: $PYTHON_CMD"

# 2. PyInstaller kurulumu (Yol sorununu asmak icin -m pip kullanilir)
echo "PyInstaller ve pygame-ce kontrol ediliyor/kuruluyor..."
$PYTHON_CMD -m pip install pyinstaller pygame-ce

# 3. Build (Yol sorununu asmak icin -m PyInstaller kullanilir)
echo "Derleniyor..."
$PYTHON_CMD -m PyInstaller CumleKurmaYarisi.spec --clean --noconfirm

echo ""
echo "=== Build tamamlandi! ==="
echo "Dosya konumu: dist/Devrilmeyen Cümle"
echo ""
echo "NOT: Eger Windows kullaniyorsaniz lutfen 'build.bat' dosyasina cift tiklayin."