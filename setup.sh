#!/bin/bash

# ==========================================
# KONFIGURASI UMUM
# ==========================================
REPO="https://raw.githubusercontent.com/DOT-SUNDA/AUTO-SHARE/refs/heads/main"
DIR="/root/auto"

# Warna Output
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

# Deteksi IP untuk laporan akhir
IP=$(curl -s ifconfig.me || hostname -I | awk '{print $1}')

clear
echo -e "${CYAN}====================================================${NC}"
echo -e "${CYAN}       AUTO SETUP IDX BOT (STATIC URL)             ${NC}"
echo -e "${CYAN}====================================================${NC}"

NEED_REBOOT=false

# ==========================================
# 1. SYSTEM & DEPENDENCIES
# ==========================================
# Mengatur frontend agar tidak muncul dialog interaktif saat install
export DEBIAN_FRONTEND=noninteractive

if ! command -v xvfb &> /dev/null; then
    echo -e "${GREEN}>>> Installing System Dependencies...${NC}"
    apt-get update -qq
    apt-get install -y -qq wget curl unzip gnupg2 jq python3-pip python3-venv \
    python3-dev python3-tk xvfb xauth scrot libxi6 gnome-screenshot xclip
else
    echo -e "✅ Dependencies system sudah terinstall."
fi

# ==========================================
# 2. VALIDASI CHROME 109
# ==========================================
CURRENT_VER=$(google-chrome --version 2>/dev/null | awk '{print $3}' | cut -d. -f1)

if [ "$CURRENT_VER" == "109" ]; then
    echo -e "✅ Chrome 109 sudah terinstall. Melewati instalasi Chrome..."
else
    echo -e "${RED}⚠️  Chrome versi $CURRENT_VER terdeteksi (atau tidak ada).${NC}"
    echo -e ">>> Menghapus versi lama & Menginstall Chrome 109..."
    
    # Hapus bersih versi lain
    apt-get remove -y google-chrome-stable google-chrome-beta google-chrome-unstable > /dev/null 2>&1
    apt-get purge -y google-chrome-stable > /dev/null 2>&1
    rm -f /etc/apt/sources.list.d/google-chrome.list

    # Download versi 109 dari arsip
    echo ">>> Downloading Chrome 109..."
    wget -q -O /tmp/chrome109.deb https://mirror.cs.uchicago.edu/google-chrome/pool/main/g/google-chrome-stable/google-chrome-stable_109.0.5414.74-1_amd64.deb

    # Install
    apt-get install -y /tmp/chrome109.deb
    apt-get install -f -y # Fix dependencies jika ada error

    # Bersihkan file installer
    rm -f /tmp/chrome109.deb

    # Kunci versi agar tidak auto-update
    apt-mark hold google-chrome-stable
    
    # Set flag reboot karena habis install core system
    NEED_REBOOT=true
fi

# ==========================================
# 3. INSTALL PYTHON LIBRARIES
# ==========================================
echo -e "\n${GREEN}[+] Install Python Libraries...${NC}"
pip3 install flask selenium pyautogui psutil requests pyperclip --break-system-packages --ignore-installed

# ==========================================
# 4. DOWNLOAD SCRIPT & SETUP SERVICE
# ==========================================
mkdir -p "$DIR"
cd "$DIR" || exit

echo -e "\n${GREEN}[+] Mendownload script dari Repository...${NC}"
echo -e "Source: $REPO"
wget -q -O main.py "$REPO/main.py"
wget -q -O agent.py "$REPO/agent.py"

echo -e "\n${GREEN}[+] Membuat Systemd Service (ghost-agent)...${NC}"
cat > /etc/systemd/system/ghost-agent.service <<EOF
[Unit]
Description=Ghost Bot
After=network.target

[Service]
User=root
WorkingDirectory=$DIR
ExecStart=/usr/bin/python3 $DIR/agent.py
Restart=always
RestartSec=5
StandardOutput=append:$DIR/service.log
StandardError=append:$DIR/service_error.log

[Install]
WantedBy=multi-user.target
EOF

# Reload daemon dan enable service
systemctl daemon-reload
systemctl enable ghost-agent

# ==========================================
# 5. FINISHING
# ==========================================
if [ "$NEED_REBOOT" = true ]; then
    MSG="✅ <b>INSTALL COMPLETED (Chrome Updated)</b>%0AIP: <code>$IP</code>%0AStatus: <b>Rebooting...</b>"
    echo -e "\n${RED}>>> System perlu reboot untuk menerapkan perubahan Chrome.${NC}"
    echo -e ">>> Rebooting in 3 seconds..."
    sleep 3
    reboot
else
    # Jika tidak perlu reboot, restart service bot saja agar update applied
    echo -e "\n${GREEN}>>> Script updated. Service restarted.${NC}"
    systemctl restart ghost-agent
fi
