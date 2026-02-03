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
# HTML + CSS Bootstrap 5 (Professional UI Upgrade)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Control Panel Bot</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet">
    
    <style>
        :root {
            --primary-color: #4361ee;
            --primary-hover: #3a56d4;
            --bg-color: #f3f4f6;
            --card-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.05);
        }
        
        body {
            background-color: var(--bg-color);
            font-family: 'Inter', sans-serif;
            color: #1f2937;
            padding-bottom: 40px;
        }

        /* Navbar Sederhana */
        .navbar {
            background-color: #ffffff;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 1rem 0;
            margin-bottom: 2rem;
        }
        .navbar-brand {
            font-weight: 700;
            color: #111827;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .status-badge {
            font-size: 0.75rem;
            padding: 0.35em 0.65em;
            border-radius: 50rem;
            background-color: #d1fae5;
            color: #065f46;
            font-weight: 600;
        }

        /* Card Container */
        .main-card {
            border: none;
            border-radius: 16px;
            background: #ffffff;
            box-shadow: var(--card-shadow);
            overflow: hidden;
        }
        .card-header-custom {
            background: #ffffff;
            padding: 2rem 2rem 1rem 2rem;
            border-bottom: none;
        }
        .card-body-custom {
            padding: 1rem 2rem 2rem 2rem;
        }

        /* Form Elements */
        .form-control {
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 0.75rem 1rem;
            font-size: 0.95rem;
        }
        .form-control:focus {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 4px rgba(67, 97, 238, 0.1);
        }
        
        /* Area Input Akun (Code Style) */
        textarea.account-box {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            background-color: #f8fafc;
            color: #334155;
            border-color: #e2e8f0;
            line-height: 1.6;
        }

        /* Tombol */
        .btn-primary-custom {
            background-color: var(--primary-color);
            border: none;
            padding: 12px 24px;
            font-weight: 600;
            border-radius: 8px;
            transition: all 0.2s ease;
            width: 100%;
        }
        .btn-primary-custom:hover {
            background-color: var(--primary-hover);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(67, 97, 238, 0.2);
        }
        .btn-primary-custom:active {
            transform: translateY(0);
        }

        /* Alert Messages */
        .alert {
            border: none;
            border-radius: 10px;
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.03);
        }
        .alert-success { background-color: #ecfdf5; color: #065f46; }
        .alert-danger { background-color: #fef2f2; color: #991b1b; }
        
        .footer-text {
            font-size: 0.8rem;
            color: #9ca3af;
            text-align: center;
            margin-top: 2rem;
        }
    </style>
</head>
<body>

    <nav class="navbar">
        <div class="container">
            <span class="navbar-brand">
                <i class="bi bi-robot text-primary" style="font-size: 1.5rem;"></i>
                XVFB Bot Controller
                <span class="status-badge"><i class="bi bi-circle-fill" style="font-size: 6px; vertical-align: middle; margin-right:4px;"></i> Active</span>
            </span>
        </div>
    </nav>

    <div class="container">
        <div class="row justify-content-center">
            <div class="col-lg-7 col-md-9">

                {% with messages = get_flashed_messages(with_categories=true) %}
                  {% if messages %}
                    {% for category, message in messages %}
                      <div class="alert alert-{{ category }} alert-dismissible fade show mb-4" role="alert">
                        {% if category == 'success' %}
                            <i class="bi bi-check-circle-fill me-2 fs-5"></i>
                        {% else %}
                            <i class="bi bi-exclamation-triangle-fill me-2 fs-5"></i>
                        {% endif %}
                        <div>{{ message }}</div>
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                      </div>
                    {% endfor %}
                  {% endif %}
                {% endwith %}

                <div class="main-card">
                    <div class="card-header-custom">
                        <h4 class="fw-bold mb-1">Konfigurasi Worker</h4>
                        <p class="text-muted small mb-0">Perbarui target dan kredensial akun untuk proses otomatisasi.</p>
                    </div>
                    
                    <div class="card-body-custom">
                        <form method="POST">
                            
                            <div class="mb-4">
                                <label class="form-label fw-bold small text-uppercase text-muted ls-1">Email Target</label>
                                <div class="input-group">
                                    <span class="input-group-text bg-white border-end-0 text-muted"><i class="bi bi-envelope"></i></span>
                                    <input type="email" class="form-control border-start-0 ps-0" name="target_email" 
                                           value="{{ current_target }}" placeholder="admin@target.com" required>
                                </div>
                            </div>

                            <div class="mb-4">
                                <div class="d-flex justify-content-between align-items-center mb-2">
                                    <label class="form-label fw-bold small text-uppercase text-muted ls-1 mb-0">List Akun</label>
                                    <span class="badge bg-light text-secondary border">Format: email:password</span>
                                </div>
                                <textarea class="form-control account-box" name="accounts" rows="10" 
                                          placeholder="user01@mail.com:rahasia123&#10;user02@mail.com:rahasia456" required>{{ current_accounts }}</textarea>
                                <div class="form-text mt-2"><i class="bi bi-info-circle me-1"></i> Satu akun per baris. Pastikan tidak ada spasi berlebih.</div>
                            </div>

                            <div class="d-grid mt-5">
                                <button type="submit" class="btn btn-primary btn-primary-custom shadow-sm">
                                    <i class="bi bi-play-circle-fill me-2"></i> Simpan & Jalankan Bot
                                </button>
                            </div>

                        </form>
                    </div>
                </div>

                <div class="footer-text">
                    <p class="mb-0">System Port: 80 &bull; Worker Script: <code>{{ worker_name }}</code></p>
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
                
            idx_file_path = os.path.join(BASE_DIR, 'idx_project_urls.txt')
            with open(idx_file_path, 'w') as f:
                f.write('')    

            # 3. Jalankan Worker dengan xvfb-run (Background Process)
            if os.path.exists(WORKER_SCRIPT):
                # xvfb-run -a (auto server num) agar tidak bentrok
                cmd = f"xvfb-run -a python3 {WORKER_SCRIPT}"
                subprocess.Popen(cmd, shell=True, cwd=BASE_DIR, 
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                flash(f'Sukses! Data disimpan & Bot dijalankan untuk: {target_email}', 'success')
            else:
                flash(f'Error: File {WORKER_SCRIPT} tidak ditemukan!', 'danger')

        except Exception as e:
            flash(f'Terjadi kesalahan: {str(e)}', 'danger')
        
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
                                  worker_name="main.py")

# ================= M A I N =================
if __name__ == '__main__':
    # Host 0.0.0.0 agar bisa diakses public IP
    # Port 80 (HTTP Standar)
    print("🌐 Panel berjalan di Port 80...")
    app.run(host='0.0.0.0', port=80)
