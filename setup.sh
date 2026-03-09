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
YELLOW='\033[1;33m'
NC='\033[0m'

# Deteksi IP untuk laporan akhir
IP=$(curl -s ifconfig.me || hostname -I | awk '{print $1}')

clear
echo -e "${CYAN}====================================================${NC}"
echo -e "${CYAN}      AUTO SETUP GHOST DOT PANEL - MULTI OS         ${NC}"
echo -e "${CYAN}====================================================${NC}"

NEED_REBOOT=false

# ==========================================
# 1. DETEKSI SISTEM OPERASI
# ==========================================
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    OS_FAMILY=$ID_LIKE
else
    echo -e "${RED}Tidak dapat mendeteksi Sistem Operasi.${NC}"
    exit 1
fi

echo -e "${GREEN}>>> Mendeteksi OS: $PRETTY_NAME${NC}"

# ==========================================
# 2. SYSTEM & DEPENDENCIES (NO FIREWALL)
# ==========================================
if ! command -v xvfb &> /dev/null; then
    echo -e "${GREEN}>>> Installing System Dependencies...${NC}"
    
    # --- LOGIKA DEBIAN / UBUNTU ---
    if [[ "$OS" == "ubuntu" || "$OS" == "debian" || "$OS_FAMILY" == *"debian"* ]]; then
        export DEBIAN_FRONTEND=noninteractive
        apt-get update -qq
        apt-get install -y -qq wget curl unzip gnupg2 jq python3-pip python3-venv \
        python3-dev python3-tk xvfb xauth scrot libxi6 gnome-screenshot xclip
        
    # --- LOGIKA ALMALINUX / CENTOS / RHEL ---
    elif [[ "$OS" == "almalinux" || "$OS" == "centos" || "$OS_FAMILY" == *"rhel"* || "$OS" == "rocky" ]]; then
        dnf install -y epel-release
        dnf update -y
        dnf install -y wget curl unzip gnupg2 jq python3-pip python3-devel \
        python3-tkinter xorg-x11-server-Xvfb xauth scrot libXi gnome-screenshot xclip python3-dnf-plugin-versionlock
    else
        echo -e "${RED}OS ini belum didukung penuh oleh script.${NC}"
        exit 1
    fi
else
    echo -e "✅ Dependencies system sudah terinstall."
fi

# ==========================================
# 2.5 OPTIMASI SISTEM (SAFE MODE - NO NETWORK TOUCHED)
# ==========================================
echo -e "\n${GREEN}[+] Melakukan Optimasi Sistem (Safe Mode)...${NC}"

# Membatasi ukuran log systemd maksimal 50MB agar disk tidak gampang penuh
journalctl --vacuum-size=50M > /dev/null 2>&1

if [[ "$OS" == "ubuntu" || "$OS" == "debian" || "$OS_FAMILY" == *"debian"* ]]; then
    # Mematikan dan menghapus Snapd (Sangat memakan RAM di Ubuntu, aman dihapus)
    if command -v snap &> /dev/null; then
        systemctl stop snapd snapd.socket snapd.seeded > /dev/null 2>&1
        systemctl disable snapd snapd.socket snapd.seeded > /dev/null 2>&1
        apt-get remove --purge -y snapd > /dev/null 2>&1
    fi
    
    # Menghapus layanan tidak berguna (Hanya modemmanager, tidak menyentuh ssh/network)
    apt-get remove --purge -y modemmanager > /dev/null 2>&1
    
    # Membersihkan cache dan package yatim
    apt-get autoremove -y > /dev/null 2>&1
    apt-get clean > /dev/null 2>&1

elif [[ "$OS" == "almalinux" || "$OS" == "centos" || "$OS_FAMILY" == *"rhel"* || "$OS" == "rocky" ]]; then
    # Membersihkan cache dnf dan package yatim
    dnf clean all > /dev/null 2>&1
    dnf autoremove -y > /dev/null 2>&1
fi
echo -e "✅ Sistem berhasil diringankan tanpa menyentuh koneksi."

# ==========================================
# 3. VALIDASI CHROME 109
# ==========================================
CURRENT_VER=$(google-chrome --version 2>/dev/null | awk '{print $3}' | cut -d. -f1)

if [ "$CURRENT_VER" == "109" ]; then
    echo -e "✅ Chrome 109 sudah terinstall. Melewati instalasi Chrome..."
else
    echo -e "${RED}⚠️  Chrome versi $CURRENT_VER terdeteksi (atau tidak ada).${NC}"
    echo -e ">>> Menghapus versi lama & Menginstall Chrome 109..."
    
    # --- LOGIKA DEBIAN / UBUNTU ---
    if [[ "$OS" == "ubuntu" || "$OS" == "debian" || "$OS_FAMILY" == *"debian"* ]]; then
        apt-get remove -y google-chrome-stable google-chrome-beta google-chrome-unstable > /dev/null 2>&1
        apt-get purge -y google-chrome-stable > /dev/null 2>&1
        rm -f /etc/apt/sources.list.d/google-chrome.list

        echo ">>> Downloading Chrome 109 (DEB)..."
        wget -q -O /tmp/chrome109.deb https://mirror.cs.uchicago.edu/google-chrome/pool/main/g/google-chrome-stable/google-chrome-stable_109.0.5414.74-1_amd64.deb
        apt-get install -y /tmp/chrome109.deb || apt-get install -f -y 
        rm -f /tmp/chrome109.deb
        apt-mark hold google-chrome-stable
        
    # --- LOGIKA ALMALINUX / CENTOS / RHEL ---
    elif [[ "$OS" == "almalinux" || "$OS" == "centos" || "$OS_FAMILY" == *"rhel"* || "$OS" == "rocky" ]]; then
        dnf remove -y google-chrome-stable google-chrome-beta google-chrome-unstable > /dev/null 2>&1
        rm -f /etc/yum.repos.d/google-chrome.repo
        
        echo ">>> Downloading Chrome 109 (RPM)..."
        wget -q -O /tmp/chrome109.rpm https://dl.google.com/linux/chrome/rpm/stable/x86_64/google-chrome-stable-109.0.5414.74-1.x86_64.rpm || wget -q -O /tmp/chrome109.rpm "https://rpmfind.net/linux/centos/8-stream/AppStream/x86_64/os/Packages/google-chrome-stable-109.0.5414.74-1.x86_64.rpm"
        
        dnf install -y /tmp/chrome109.rpm
        rm -f /tmp/chrome109.rpm
        
        # Kunci versi di RHEL
        dnf versionlock add google-chrome-stable
    fi
    
    NEED_REBOOT=true
fi

# ==========================================
# 4. INSTALL PYTHON LIBRARIES (SMART PIP)
# ==========================================
echo -e "\n${GREEN}[+] Install Python Libraries...${NC}"
PY_PACKAGES="flask selenium pyautogui psutil requests pyperclip"

# Cek apakah pip di sistem ini mendukung flag --break-system-packages
if pip3 install --help 2>&1 | grep -q "\--break-system-packages"; then
    echo -e ">>> Mode PEP-668 terdeteksi. Menggunakan --break-system-packages..."
    pip3 install $PY_PACKAGES --break-system-packages --ignore-installed
else
    echo -e ">>> Menggunakan instalasi pip standar..."
    pip3 install $PY_PACKAGES --ignore-installed || pip3 install $PY_PACKAGES
fi

# ==========================================
# 5. DOWNLOAD SCRIPT & SETUP SERVICE
# ==========================================
mkdir -p "$DIR"
cd "$DIR" || exit

echo -e "\n${GREEN}[+] Mendownload script dari Repository...${NC}"
wget -q -O agent.py "$REPO/agent.py"
wget -q -O main.py "$REPO/main.py"

echo -e "\n${GREEN}[+] Membuat Systemd Service (dot-auto)...${NC}"
cat > /etc/systemd/system/dot-auto.service <<EOF
[Unit]
Description=GHOST DOT Web Panel Service
After=network.target

[Service]
User=root
WorkingDirectory=$DIR
ExecStart=/usr/bin/python3 $DIR/agent.py
Restart=always
RestartSec=5
StandardOutput=append:$DIR/panel_service.log
StandardError=append:$DIR/panel_error.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable dot-auto

# ==========================================
# 6. MEMBUAT SHORTCUT COMMAND (DOTAUTO)
# ==========================================
echo -e "\n${GREEN}[+] Membuat shortcut command 'dotauto'...${NC}"

cat > /usr/local/bin/dotauto <<'EOF'
#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SERVICE="dot-auto"

case "$1" in
    start)
        echo -e "${GREEN}>>> Menyalakan Web Panel...${NC}"
        systemctl start $SERVICE
        echo -e "✅ Panel Berjalan."
        ;;
    stop)
        echo -e "${RED}>>> Mematikan Web Panel...${NC}"
        systemctl stop $SERVICE
        echo -e "🛑 Panel Berhenti."
        # Memastikan worker main.py juga mati jika panel dimatikan
        pkill -f "main.py" > /dev/null 2>&1
        ;;
    restart)
        echo -e "${YELLOW}>>> Merestart Web Panel...${NC}"
        systemctl restart $SERVICE
        echo -e "✅ Panel berhasil direstart."
        ;;
    log)
        echo -e "${CYAN}>>> Menampilkan Log Panel (Tekan CTRL+C untuk keluar)...${NC}"
        tail -f /root/auto/panel_service.log
        ;;
    status)
        systemctl status $SERVICE --no-pager
        ;;
    *)
        echo -e "Usage: dotauto {start|stop|restart|log|status}"
        exit 1
        ;;
esac
EOF

chmod +x /usr/local/bin/dotauto

# ==========================================
# 7. FINISHING
# ==========================================
if [ "$NEED_REBOOT" = true ]; then
    echo -e "\n${RED}>>> System perlu reboot untuk menerapkan perubahan Chrome.${NC}"
    echo -e ">>> Rebooting in 3 seconds..."
    sleep 3
    reboot
else
    echo -e "\n${GREEN}>>> Setup Selesai. Service dot-auto diaktifkan.${NC}"
    dotauto restart
    echo -e "\n${CYAN}====================================================${NC}"
    echo -e "✅ ${GREEN}GHOST DOT PANEL SUDAH AKTIF${NC}"
    echo -e "🔗 Akses Panel di : ${YELLOW}http://$IP:2004${NC}"
    echo -e "🔑 Passkey       : ${YELLOW}jembut123${NC}"
    echo -e "${CYAN}====================================================${NC}"
    echo -e "\n${CYAN}INFO COMMAND TERMINAL:${NC}"
    echo -e "  - ${GREEN}dotauto start${NC}   : Nyalakan web panel"
    echo -e "  - ${RED}dotauto stop${NC}    : Matikan web panel & worker"
    echo -e "  - ${YELLOW}dotauto restart${NC} : Restart web panel"
    echo -e "  - ${CYAN}dotauto log${NC}     : Cek log web panel"
fi
# ==========================================
# 5. MEMBUAT SHORTCUT COMMAND (DOTAUTO)
# ==========================================
echo -e "\n${GREEN}[+] Membuat shortcut command 'dotauto'...${NC}"

# Menggunakan 'EOF' (dengan kutip) agar variabel $1 tidak dieksekusi saat pembuatan file
cat > /usr/local/bin/dotauto <<'EOF'
#!/bin/bash

# Warna
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SERVICE="ghost-agent"

case "$1" in
    start)
        echo -e "${GREEN}>>> Menyalakan Bot...${NC}"
        systemctl start $SERVICE
        echo -e "✅ Bot Berjalan."
        ;;
    stop)
        echo -e "${RED}>>> Mematikan Bot...${NC}"
        systemctl stop $SERVICE
        echo -e "🛑 Bot Berhenti."
        ;;
    restart)
        echo -e "${YELLOW}>>> Merestart Bot...${NC}"
        systemctl restart $SERVICE
        echo -e "✅ Bot berhasil direstart."
        ;;
    log)
        echo -e "${CYAN}>>> Menampilkan Log (Tekan CTRL+C untuk keluar)...${NC}"
        tail -f /root/auto/service.log
        ;;
    status)
        systemctl status $SERVICE --no-pager
        ;;
    *)
        echo -e "Usage: dotauto {start|stop|restart|log|status}"
        exit 1
        ;;
esac
EOF

# Berikan izin eksekusi
chmod +x /usr/local/bin/dotauto

# ==========================================
# 6. FINISHING
# ==========================================
if [ "$NEED_REBOOT" = true ]; then
    echo -e "\n${RED}>>> System perlu reboot untuk menerapkan perubahan Chrome.${NC}"
    echo -e ">>> Rebooting in 3 seconds..."
    sleep 3
    reboot
else
    echo -e "\n${GREEN}>>> Script updated. Service restarted.${NC}"
    # Restart bot menggunakan command baru
    dotauto restart
    echo -e "\n${CYAN}INFO COMMAND:${NC}"
    echo -e "Sekarang gunakan perintah ini:"
    echo -e "  - ${GREEN}dotauto start${NC}   : Nyalakan bot"
    echo -e "  - ${RED}dotauto stop${NC}    : Matikan bot"
    echo -e "  - ${YELLOW}dotauto restart${NC} : Restart bot"
    echo -e "  - ${CYAN}dotauto log${NC}     : Cek log error/jalan"
fi
