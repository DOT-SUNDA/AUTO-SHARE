#!/bin/bash

# ==========================================
# KONFIGURASI URL STATIC
# ==========================================
# Ganti link di bawah ini dengan link RAW script Python Anda (Github/Pastebin)
REPO="edx.dotaja.store"
DIR="/root/auto"

# ==========================================
# SYSTEM SETUP
# ==========================================
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

clear
echo -e "${CYAN}====================================================${NC}"
echo -e "${CYAN}      AUTO SETUP IDX BOT (STATIC URL)              ${NC}"
echo -e "${CYAN}====================================================${NC}"

NEED_REBOOT=false

# 1. SYSTEM & DEPENDENCIES (Cek dulu biar ga lama)
export DEBIAN_FRONTEND=noninteractive
if ! command -v xvfb &> /dev/null; then
    echo ">>> Installing System Dependencies..."
    apt-get update -qq
    apt-get install -y -qq wget curl unzip gnupg2 jq python3-pip python3-venv python3-dev python3-tk xvfb xauth scrot libxi6 gnome-screenshot xclip
fi

# 2. VALIDASI CHROME 109 (LOGIKA CERDAS)
CURRENT_VER=$(google-chrome --version 2>/dev/null | awk '{print $3}' | cut -d. -f1)

if [ "$CURRENT_VER" == "109" ]; then
    echo "✅ Chrome 109 sudah terinstall. Melewati instalasi Chrome..."
else
    echo "⚠️ Chrome versi $CURRENT_VER terdeteksi (atau tidak ada)."
    echo ">>> Menghapus versi lama & Menginstall Chrome 109..."
    
    # Hapus bersih versi lain
    apt-get remove -y google-chrome-stable google-chrome-beta google-chrome-unstable > /dev/null 2>&1
    apt-get purge -y google-chrome-stable > /dev/null 2>&1
    rm -f /etc/apt/sources.list.d/google-chrome.list

    # Download versi 109 dari arsip
    wget -q -O /tmp/chrome109.deb https://mirror.cs.uchicago.edu/google-chrome/pool/main/g/google-chrome-stable/google-chrome-stable_109.0.5414.74-1_amd64.deb

    # Install
    apt-get install -y /tmp/chrome109.deb
    apt-get install -f -y # Fix dependencies jika ada error

    # Kunci versi
    apt-mark hold google-chrome-stable
    
    # Set flag reboot karena habis install core system
    NEED_REBOOT=true
fi

# 3. INSTALL PYTHON LIBRARIES
echo -e "\n${GREEN}[+] Install Python Libraries...${NC}"
pip3 install selenium pyautogui psutil requests pyperclip --break-system-packages --ignore-installed

# 4. DOWNLOAD MAIN.PY (STATIC)
mkdir -p "$DIR"
cd "$DIR" || exit
echo -e "\n${GREEN}[+] Mendownload main.py dari Static URL...${NC}"
echo -e "Source: $REPO"
wget -O main.py "$REPO/main.py"
wget -O agent.py "$REPO/agent.py"

cat > /etc/systemd/system/ghost-agent.service <<EOF
[Unit]
Description=Ghost Bot
After=network.target
[Service]
User=root
WorkingDirectory=$DIR
ExecStart=python3 agent.py
Restart=always
RestartSec=5
StandardOutput=append:$DIR/service.log
StandardError=append:$DIR/service_error.log
[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable ghost-agent

if [ "$NEED_REBOOT" = true ]; then
    MSG="✅ <b>INSTALL COMPLETED (Chrome Updated)</b>%0AIP: <code>$IP</code>%0AStatus: <b>Rebooting...</b>"
    reboot
else
    # Jika tidak perlu reboot, cukup restart bot
    echo ">>> Script updated. Service restarted."
fi
