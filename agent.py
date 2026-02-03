import os
import subprocess
from flask import Flask, request, render_template_string, flash, redirect, url_for

# ================= K O N F I G U R A S I =================
app = Flask(__name__)
app.secret_key = 'kuncirahasia_bot_panel_xvfb'

# Path file di folder yang sama dengan script ini
BASE_DIR = os.getcwd()
WORKER_SCRIPT = os.path.join(BASE_DIR, "main.py")
EMAIL_FILE = os.path.join(BASE_DIR, "email.txt")
TARGET_FILE = os.path.join(BASE_DIR, "target_email.txt")

# ================= T E M P L A T E H T M L =================
# HTML + CSS Bootstrap (Responsif) langsung di dalam variabel
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Panel Bot XVFB</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #eef2f7; font-family: 'Segoe UI', sans-serif; }
        .card { border: none; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }
        .header-title { color: #2c3e50; font-weight: 700; }
        .btn-run { background-color: #2ecc71; border: none; font-weight: 600; padding: 12px; }
        .btn-run:hover { background-color: #27ae60; }
        textarea { font-family: monospace; font-size: 0.9rem; background-color: #f8f9fa; }
        .footer { font-size: 0.8rem; color: #95a5a6; margin-top: 20px; text-align: center; }
    </style>
</head>
<body>
    <div class="container py-5">
        <div class="row justify-content-center">
            <div class="col-lg-6 col-md-8">
                
                <div class="text-center mb-4">
                    <h2 class="header-title">🚀 XVFB Bot Controller</h2>
                    <p class="text-muted">Update data & jalankan worker di background</p>
                </div>

                {% with messages = get_flashed_messages(with_categories=true) %}
                  {% if messages %}
                    {% for category, message in messages %}
                      <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                      </div>
                    {% endfor %}
                  {% endif %}
                {% endwith %}

                <div class="card p-4">
                    <form method="POST">
                        <div class="mb-4">
                            <label class="form-label fw-bold">🎯 Email Target (Ditimpah)</label>
                            <input type="email" class="form-control form-control-lg" name="target_email" 
                                   value="{{ current_target }}" placeholder="contoh: admin@target.com" required>
                        </div>

                        <div class="mb-4">
                            <label class="form-label fw-bold">📋 List Akun (Email:Password)</label>
                            <textarea class="form-control" name="accounts" rows="8" 
                                      placeholder="user1@mail.com:pass1&#10;user2@mail.com:pass2" required>{{ current_accounts }}</textarea>
                            <div class="form-text text-end">Satu akun per baris. Format <code>email:pass</code></div>
                        </div>

                        <div class="d-grid">
                            <button type="submit" class="btn btn-primary btn-run shadow-sm">
                                💾 Simpan & Jalankan Bot (xvfb)
                            </button>
                        </div>
                    </form>
                </div>

                <div class="footer">
                    Running on Port 80 | Worker: {{ worker_name }}
                </div>

            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# ================= R O U T I N G =================
@app.route('/', methods=['GET', 'POST'])
def index():
    # --- PROSES POST (SIMPAN & JALANKAN) ---
    if request.method == 'POST':
        raw_accounts = request.form.get('accounts', '').strip()
        target_email = request.form.get('target_email', '').strip()

        if not raw_accounts or not target_email:
            flash('⚠️ Semua kolom wajib diisi!', 'warning')
            return redirect(url_for('index'))

        try:
            # 1. Timpa file email.txt
            # Mengubah Windows newline (\r\n) menjadi Linux (\n)
            formatted_accounts = raw_accounts.replace('\r\n', '\n')
            with open(EMAIL_FILE, 'w') as f:
                f.write(formatted_accounts)
                if not formatted_accounts.endswith('\n'):
                    f.write('\n')

            # 2. Timpa file target_email.txt
            with open(TARGET_FILE, 'w') as f:
                f.write(target_email)

            # 3. Jalankan Worker dengan xvfb-run (Background Process)
            if os.path.exists(WORKER_SCRIPT):
                # xvfb-run -a (auto server num) agar tidak bentrok
                cmd = f"xvfb-run -a python3 {WORKER_SCRIPT}"
                subprocess.Popen(cmd, shell=True, cwd=BASE_DIR, 
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                flash(f'✅ Sukses! Data disimpan & Bot dijalankan untuk target: {target_email}', 'success')
            else:
                flash(f'❌ Error: File {WORKER_SCRIPT} tidak ditemukan!', 'danger')

        except Exception as e:
            flash(f'❌ Terjadi kesalahan: {str(e)}', 'danger')
        
        return redirect(url_for('index'))

    # --- PROSES GET (TAMPILKAN DATA LAMA) ---
    current_accounts = ""
    current_target = ""

    # Baca file jika ada, untuk ditampilkan kembali di form (User Friendly)
    if os.path.exists(EMAIL_FILE):
        with open(EMAIL_FILE, 'r') as f:
            current_accounts = f.read().strip()
    
    if os.path.exists(TARGET_FILE):
        with open(TARGET_FILE, 'r') as f:
            current_target = f.read().strip()

    return render_template_string(HTML_TEMPLATE, 
                                  current_accounts=current_accounts, 
                                  current_target=current_target,
                                  worker_name="worker.py")

# ================= M A I N =================
if __name__ == '__main__':
    # Host 0.0.0.0 agar bisa diakses public IP
    # Port 80 (HTTP Standar)
    print("🌐 Panel berjalan di Port 80...")
    app.run(host='0.0.0.0', port=80)
