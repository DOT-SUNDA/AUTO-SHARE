import os
import time
import random
import string
import subprocess
import psutil
import pyautogui
import requests 
import pyperclip

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

# ==========================================
# KONFIGURASI TELEGRAM
# ==========================================
TELEGRAM_BOT_TOKEN = "8455364218:AAFoy_mvhZi9HYeTM48hO9aXapE-cYmWuCs" 
TELEGRAM_CHAT_ID = "-1003647070115"

# ==========================================
# KONFIGURASI LAIN
# ==========================================
CHROME_PATH = "/usr/bin/google-chrome" 
USER_DATA_DIR = os.path.join(os.getcwd(), "chrome-hybrid") 
DEBUG_PORT = "9222"

DESKTOP_PATH = os.getcwd()
EMAIL_FILE = os.path.join(DESKTOP_PATH, "email.txt")
OUTPUT_FILE = os.path.join(DESKTOP_PATH, "idx_project_urls.txt")

# --- [UBAH DI SINI] BACA SHARE EMAIL DARI FILE ---
SHARE_EMAIL_FILE = os.path.join(DESKTOP_PATH, "target_email.txt")
try:
    with open(SHARE_EMAIL_FILE, "r") as f:
        SHARE_EMAIL = f.read().strip()
    print(f"✅ Target Share Email dimuat: {SHARE_EMAIL}")
except FileNotFoundError:
    print(f"⚠️ File {SHARE_EMAIL_FILE} tidak ditemukan! Menggunakan default.")
    SHARE_EMAIL = "axmin01@joko.nett.to"
# -------------------------------------------------

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def random_app_name(prefix="bahlil"):
    rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k=3))
    return f"{prefix}{rand}"

def send_telegram_photo(driver, caption_text):
    """
    Fungsi screenshot menggunakan SELENIUM.
    """
    try:
        screenshot_path = os.path.join(DESKTOP_PATH, "login_screenshot.png")
        
        driver.save_screenshot(screenshot_path)
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        files = {'photo': open(screenshot_path, 'rb')}
        data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption_text}
        
        response = requests.post(url, files=files, data=data)
        
        if response.status_code == 200:
            print("📸 Screenshot terkirim ke Telegram!")
        else:
            print(f"⚠️ Gagal kirim Telegram: {response.text}")
            
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)
            
    except Exception as e:
        print(f"❌ Error fungsi screenshot: {e}")

# --- [BARU] FUNGSI KIRIM FILE TXT KE TELEGRAM ---
def send_telegram_document(file_path):
    """
    Mengirim file txt berisi kumpulan link ke Telegram
    """
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
        
        # 'files' tuple format: ('nama_file_di_telegram.txt', open_file_object)
        # Nama file static di set di sini: "result_all_links.txt"
        files = {'document': ('result_all_links.txt', open(file_path, 'rb'))}
        data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': "✅ Proses Selesai. Berikut list semua link project."}
        
        response = requests.post(url, files=files, data=data)
        
        if response.status_code == 200:
            print("📁 File TXT berhasil dikirim ke Telegram!")
        else:
            print(f"⚠️ Gagal kirim file: {response.text}")
    except Exception as e:
        print(f"❌ Error fungsi kirim file: {e}")

# ==========================================
# LOAD DATA
# ==========================================
ACCOUNTS = []
try:
    with open(EMAIL_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and ":" in line:
                parts = line.split(":", 1)
                ACCOUNTS.append((parts[0].strip(), parts[1].strip()))
except FileNotFoundError:
    print(f"❌ File {EMAIL_FILE} tidak ditemukan!")
    exit()

if not ACCOUNTS:
    print("❌ Tidak ada akun yang dimuat.")
    exit()

# ==========================================
# MAIN LOOP
# ==========================================
for EMAIL, CURRENT_PASSWORD in ACCOUNTS:
    print("\n==============================")
    print(f"🔑 LOGIN EMAIL: {EMAIL}")
    print("==============================")

    # STEP 1 — BUKA CHROME
    chrome_process = subprocess.Popen([
        CHROME_PATH,
        "--no-sandbox", "--disable-dev-shm-usage", "--start-maximized",
        "--test-type",
        "--simulate-outdated-no-au='Tue, 31 Dec 2099 23:59:59 GMT'",
        "--disable-component-update",
        "--disable-session-crashed-bubble",
        "--incognito",
        "--no-first-run", "--no-default-browser-check", 
        f"--window-size={SCREEN_WIDTH},{SCREEN_HEIGHT}",
        f"--remote-debugging-port={DEBUG_PORT}",
        f"--user-data-dir={USER_DATA_DIR}",
        "https://idx.google.com/joko"
    ])
    time.sleep(20)

    # STEP 2 — LOGIN (PyAutoGUI)
    pyautogui.write(EMAIL, interval=0.08)
    time.sleep(1)
    pyautogui.press("enter")
    time.sleep(10)

    pyperclip.copy(CURRENT_PASSWORD)
    time.sleep(1)
    
    # Tekan Ctrl+V (Paste)
    pyautogui.hotkey('ctrl', 'v') 
    time.sleep(1)
    pyautogui.press("enter")
    time.sleep(10) 

    # --------------------------------------
    # STEP 3 — ATTACH SELENIUM
    # --------------------------------------
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{DEBUG_PORT}")
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 25)
    
    # --------------------------------------
    try:
        confirm_btn = wait.until(EC.element_to_be_clickable((By.ID, "confirm")))
        confirm_btn.click()
        print("✅ Tombol (ID: confirm) diklik")

    except TimeoutException:
        print("⚠️ ID 'confirm' tidak ada, mencari tombol 'I understand'...")
        try:
            understand_btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[.//span[contains(text(), 'I understand')]]")
            ))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", understand_btn)
            print("✅ Tombol 'I understand' berhasil diklik!")
            
        except TimeoutException:
            print("❌ Tombol 'Saya mengerti' tidak ditemukan sama sekali, lanjut...")

    print("📸 Mengambil screenshot login...")
    send_telegram_photo(driver, f"Login Status: {EMAIL}")

    driver.get("https://idx.google.com")
    time.sleep(8)

    try:
        terms_input = WebDriverWait(driver, 40).until(
            EC.presence_of_element_located((By.ID, "utos-checkbox"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", terms_input)
        time.sleep(1)
    except TimeoutException:
        print("❌ Checkbox Terms IDX tidak muncul")

    try:
        confirm_button = WebDriverWait(driver, 40).until(
            EC.presence_of_element_located((By.ID, "submit-button"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].disabled = false; arguments[0].click();", confirm_button)
        print("✅ IDX Confirm selesai")
    except TimeoutException:
        print("❌ Confirm button IDX tidak muncul")
    
    time.sleep(8)

    # --------------------------------------
    # STEP 8 + 9 LOOP 2X — BUAT PROJECT
    # --------------------------------------
    for i in range(2):
        driver.get("https://idx.google.com/new/flutter")
        time.sleep(5)
        app_name = random_app_name()

        try:
            app_input = WebDriverWait(driver, 40).until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='My Flutter App']")))
            driver.execute_script(f"arguments[0].value = '{app_name}'; arguments[0].dispatchEvent(new Event('input', {{ bubbles: true }})); arguments[0].dispatchEvent(new Event('change', {{ bubbles: true }}));", app_input)
            print(f"✅ App name diisi: {app_name}")
        except TimeoutException:
            print("❌ Input nama app tidak muncul")
            continue

        try:
            create_button = WebDriverWait(driver, 40).until(EC.presence_of_element_located((By.ID, "create-button")))
            driver.execute_script("arguments[0].disabled = false; arguments[0].click();", create_button)
            print("🚀 Create Flutter project diklik")
        except TimeoutException:
            print("❌ Tombol Create tidak muncul")
            continue

        time.sleep(10)
        project_url = driver.current_url
        print(f"🌐 Project URL: {project_url}")

        with open(OUTPUT_FILE, "a") as f:
            f.write(f"{project_url}\n")

    # =========================================================
    # STEP 10 — LOGIKA SHARING
    # =========================================================
    driver.get("https://idx.google.com")
    time.sleep(5) 

    def process_sharing(kebab_btn, idx, tipe_stack):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", kebab_btn)
            time.sleep(1)
            ActionChains(driver).move_to_element(kebab_btn).click().perform()
            time.sleep(1)
            ActionChains(driver).send_keys(Keys.ARROW_DOWN).pause(0.5).send_keys(Keys.ENTER).perform()
            time.sleep(4)

            try:
                input_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Add people']")))
                input_field.send_keys(SHARE_EMAIL)
                input_field.send_keys(Keys.ENTER)
                time.sleep(2)
                
                share_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and .//span[contains(text(), 'Share')]]")))
                share_btn.click()
                print(f"✅ [{tipe_stack}] Sukses Share ke {SHARE_EMAIL}")
                time.sleep(3)
            except TimeoutException:
                print(f"❌ [{tipe_stack}] Gagal input/share")
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        except Exception as e:
            print(f"⚠️ [{tipe_stack}] Error: {e}")

    try:
        stack3_btns = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//button[@type='button' and @data-cdk-menu-stack-id='cdk-menu-stack-3']")))
        print(f"🔎 Ditemukan {len(stack3_btns)} tombol STACK-3")
        for i, btn in enumerate(stack3_btns):
            process_sharing(btn, i, "STACK-3")
    except TimeoutException:
        print("❌ Tidak ditemukan tombol STACK-3")

    print("\n⏳ Menunggu 10 detik...")
    time.sleep(10)

    try:
        stack4_btns = driver.find_elements(By.XPATH, "//button[@type='button' and @data-cdk-menu-stack-id='cdk-menu-stack-4']")
        print(f"🔎 Ditemukan {len(stack4_btns)} tombol STACK-4")
        if len(stack4_btns) > 0:
            for i, btn in enumerate(stack4_btns):
                process_sharing(btn, i, "STACK-4")
    except Exception as e:
        print(f"❌ Error STACK-4: {e}")

    # CLEANUP PER AKUN
    time.sleep(5)
    print("\n🛑 Cleanup...")
    try:
        driver.quit()
    except: pass
    try:
        chrome_process.terminate()
    except: pass
    time.sleep(5)

# ==========================================
# FINAL STEP: KIRIM FILE HASIL KE TELEGRAM
# ==========================================
print("\n==============================")
print("🏁 SEMUA AKUN SELESAI DIPROSES")
print("==============================")

if os.path.exists(OUTPUT_FILE):
    print("🚀 Mengirim file hasil ke Telegram...")
    send_telegram_document(OUTPUT_FILE)
else:
    print("⚠️ File output link tidak ditemukan, tidak ada yang dikirim.")
