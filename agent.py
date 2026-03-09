import os
import subprocess
from functools import wraps
from flask import Flask, request, render_template_string, flash, redirect, url_for, session, jsonify

# ================= K O N F I G U R A S I =================
app = Flask(__name__)
app.secret_key = 'kuncirahasia_bot_panel_xvfb'

# Password untuk akses panel
PANEL_PASSWORD = 'jembut123'

# --- PERBAIKAN PATH ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

WORKER_SCRIPT = os.path.join(BASE_DIR, "main.py")
EMAIL_FILE = os.path.join(BASE_DIR, "email.txt")
TARGET_FILE = os.path.join(BASE_DIR, "target_email.txt")
REPO_FILE = os.path.join(BASE_DIR, "repo_url.txt")
IDX_FILE = os.path.join(BASE_DIR, 'idx_project_urls.txt')
LOG_FILE = os.path.join(BASE_DIR, 'worker.log') # File untuk live log

# ================= HELPER FUNCTIONS =================
def is_worker_running():
    """Mengecek apakah main.py sedang berjalan di background"""
    try:
        # Cek process list di linux khusus untuk nama script ini (abaikan proses grep)
        output = subprocess.check_output(f"ps -ef | grep '{WORKER_SCRIPT}' | grep -v grep", shell=True)
        return len(output.strip()) > 0
    except subprocess.CalledProcessError:
        return False

# ================= T E M P L A T E H T M L =================

# Template Login
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="id" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login | GHOST AUTO SHARE DOT</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { background-color: #0f172a; font-family: 'Inter', sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; color: #f8fafc;}
        .login-card { background: #1e293b; padding: 2.5rem; border-radius: 16px; box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.5); border: 1px solid #334155; width: 100%; max-width: 400px; margin: 15px;}
        .form-control { background-color: #0f172a; border-color: #334155; color: #f8fafc;}
        .form-control:focus { background-color: #0f172a; border-color: #6366f1; box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.15); color: #f8fafc;}
        .input-group-text { background-color: #0f172a; border-color: #334155; color: #94a3b8;}
        .btn-primary-custom { background-color: #6366f1; border: none; padding: 12px; font-weight: 600; border-radius: 8px; width: 100%; color: white; margin-top: 1rem; transition: all 0.2s;}
        .btn-primary-custom:hover { background-color: #4f46e5; transform: translateY(-1px); box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.3);}
        .ghost-icon { font-size: 3.5rem; color: #6366f1; filter: drop-shadow(0 0 10px rgba(99, 102, 241, 0.5));}
    </style>
</head>
<body>
    <div class="login-card">
        <div class="text-center mb-4">
            <i class="bi bi-incognito ghost-icon"></i>
            <h4 class="fw-bold mt-3 mb-1" style="letter-spacing: 1px;">GHOST DOT</h4>
            <p class="text-muted small">System Authentication</p>
        </div>
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="alert alert-{{ category }} small py-2 bg-opacity-10 border-0 text-{{ category }}">{{ message }}</div>
            {% endfor %}
          {% endif %}
        {% endwith %}
        <form method="POST">
            <div class="mb-4">
                <label class="form-label small fw-bold text-muted text-uppercase" style="letter-spacing: 1px;">Passkey</label>
                <div class="input-group">
                    <span class="input-group-text border-end-0"><i class="bi bi-key"></i></span>
                    <input type="password" name="password" class="form-control border-start-0 ps-0" placeholder="••••••••" required>
                </div>
            </div>
            <button type="submit" class="btn btn-primary-custom"><i class="bi bi-unlock-fill me-2"></i> Akses Panel</button>
        </form>
    </div>
</body>
</html>
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GHOST AUTO SHARE DOT</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet">
    
    <style>
        :root {
            --primary-color: #6366f1;
            --primary-hover: #4f46e5;
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --border-color: #334155;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --card-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.5);
        }
        
        body { background-color: var(--bg-color); font-family: 'Inter', sans-serif; color: var(--text-main); padding-bottom: 40px; }

        .navbar { background-color: rgba(30, 41, 59, 0.8); backdrop-filter: blur(10px); border-bottom: 1px solid var(--border-color); padding: 1rem 0; margin-bottom: 2.5rem; position: sticky; top: 0; z-index: 1000; }
        .navbar-brand { font-weight: 700; color: var(--text-main); display: flex; align-items: center; gap: 12px; letter-spacing: 0.5px; }
        .brand-icon { color: var(--primary-color); font-size: 1.6rem; filter: drop-shadow(0 0 8px rgba(99, 102, 241, 0.6)); }
        
        /* Pulse status anim */
        .pulse-badge {
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
            70% { box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
            100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }
        .spin-animation { display: inline-block; animation: spin 1s linear infinite; }
        @keyframes spin { 100% { transform: rotate(360deg); } }

        .main-card { border: 1px solid var(--border-color); border-radius: 16px; background: var(--card-bg); box-shadow: var(--card-shadow); overflow: hidden; height: 100%;}
        .card-header-custom { background: transparent; padding: 2rem 2rem 1rem 2rem; border-bottom: 1px solid rgba(255,255,255,0.05); }
        .card-body-custom { padding: 1.5rem 2rem 2rem 2rem; }

        .form-control { background-color: var(--bg-color); border: 1px solid var(--border-color); border-radius: 8px; padding: 0.85rem 1rem; font-size: 0.95rem; color: var(--text-main); transition: all 0.2s; }
        .form-control:focus { background-color: var(--bg-color); border-color: var(--primary-color); box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.15); color: var(--text-main); }
        .input-group-text { background-color: var(--bg-color); border-color: var(--border-color); color: var(--text-muted); }
        .form-control::placeholder { color: #475569; }
        
        textarea.account-box { font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; background-color: #020617; color: #38bdf8; border: 1px solid var(--border-color); line-height: 1.6; }
        textarea.account-box:focus { background-color: #020617; color: #38bdf8; }

        .btn-primary-custom { background-color: var(--primary-color); border: none; padding: 14px 24px; font-weight: 600; border-radius: 8px; transition: all 0.3s ease; width: 100%; letter-spacing: 0.5px; text-transform: uppercase; }
        .btn-primary-custom:hover:not(:disabled) { background-color: var(--primary-hover); transform: translateY(-2px); box-shadow: 0 8px 20px rgba(99, 102, 241, 0.4); }
        .btn-primary-custom:disabled { background-color: #475569; color: #94a3b8; cursor: not-allowed; opacity: 0.8; }
        
        /* Terminal Log CSS */
        .terminal-box { background: #020617; border: 1px solid var(--border-color); border-radius: 16px; overflow: hidden; box-shadow: inset 0 2px 10px rgba(0,0,0,0.5); }
        .terminal-header { background: #0f172a; padding: 16px 20px; font-size: 0.85rem; font-family: 'Inter', sans-serif; font-weight: 600; color: var(--text-muted); border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center; }
        .terminal-body { padding: 15px 20px; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: #34d399; height: 500px; overflow-y: auto; margin: 0; white-space: pre-wrap; word-break: break-all; }
        .terminal-body::-webkit-scrollbar { width: 8px; }
        .terminal-body::-webkit-scrollbar-track { background: #020617; }
        .terminal-body::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
        .terminal-body::-webkit-scrollbar-thumb:hover { background: #475569; }

        .custom-label { font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1.5px; color: var(--text-muted); margin-bottom: 0.5rem; display: block; }
        
        .alert { border: 1px solid transparent; border-radius: 12px; font-size: 0.9rem; display: flex; align-items: center; background-color: rgba(255,255,255,0.05); backdrop-filter: blur(5px); }
        .alert-success { border-color: rgba(16, 185, 129, 0.3); color: #34d399; background-color: rgba(16, 185, 129, 0.1); }
        .alert-danger, .alert-warning { border-color: rgba(239, 68, 68, 0.3); color: #f87171; background-color: rgba(239, 68, 68, 0.1); }
        .footer-text { font-size: 0.8rem; color: var(--text-muted); text-align: center; margin-top: 2rem; font-family: 'JetBrains Mono', monospace; }
    </style>
</head>
<body>

    <nav class="navbar">
        <div class="container-fluid px-4 d-flex justify-content-between align-items-center">
            <span class="navbar-brand">
                <i class="bi bi-cpu-fill brand-icon"></i>
                <span class="d-none d-sm-inline">GHOST AUTO SHARE DOT</span>
                <span class="d-inline d-sm-none">GHOST DOT</span>
            </span>
            <a href="{{ url_for('logout') }}" class="btn btn-sm btn-outline-danger rounded-pill px-3 fw-medium" style="border-color: rgba(239, 68, 68, 0.5); color: #f87171;">
                <i class="bi bi-power"></i> <span class="d-none d-sm-inline ms-1">Disconnect</span>
            </a>
        </div>
    </nav>

    <div class="container-fluid px-4">
        
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="alert alert-{{ category }} alert-dismissible fade show mb-4 shadow-sm" role="alert">
                {% if category == 'success' %}
                    <i class="bi bi-check2-circle me-3 fs-4"></i>
                {% else %}
                    <i class="bi bi-exclamation-octagon me-3 fs-4"></i>
                {% endif %}
                <div class="fw-medium">{{ message }}</div>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="alert" aria-label="Close"></button>
              </div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        <div class="row g-4">
            <div class="col-lg-5 col-xl-4">
                <div class="main-card">
                    <div class="card-header-custom">
                        <h4 class="fw-bold mb-1 text-white">System Config</h4>
                        <p class="text-muted small mb-0">Atur parameter injeksi untuk worker.</p>
                    </div>
                    
                    <div class="card-body-custom pt-3">
                        <form method="POST">
                            <div class="mb-4">
                                <label class="custom-label">Target Email Share</label>
                                <div class="input-group shadow-sm">
                                    <span class="input-group-text border-end-0"><i class="bi bi-envelope-at"></i></span>
                                    <input type="email" class="form-control border-start-0 ps-0" name="target_email" 
                                           value="{{ current_target }}" placeholder="admin@ghost.net" required>
                                </div>
                            </div>
                            
                            <div class="mb-4">
                                <label class="custom-label">Github Repository URL</label>
                                <div class="input-group shadow-sm">
                                    <span class="input-group-text border-end-0"><i class="bi bi-github"></i></span>
                                    <input type="url" class="form-control border-start-0 ps-0" name="repo_url" 
                                           value="{{ current_repo }}" placeholder="https://github.com/user/project" required>
                                </div>
                            </div>

                            <div class="mb-4">
                                <div class="d-flex justify-content-between align-items-center mb-2">
                                    <label class="custom-label mb-0">Database Akun</label>
                                    <span class="badge border border-secondary text-secondary" style="background: rgba(255,255,255,0.05);">email:pass</span>
                                </div>
                                <textarea class="form-control account-box shadow-sm" name="accounts" rows="8" 
                                          placeholder="user01@mail.com:rahasia123&#10;user02@mail.com:rahasia456" required>{{ current_accounts }}</textarea>
                            </div>

                            <div class="d-grid mt-4 gap-2">
                                <button type="submit" id="btn-deploy" class="btn btn-primary-custom shadow">
                                    <i class="bi bi-rocket-takeoff-fill me-2"></i> Deploy Worker
                                </button>
                                <button type="button" id="btn-stop" class="btn btn-outline-danger shadow-sm d-none fw-bold" onclick="forceStop()">
                                    <i class="bi bi-stop-circle-fill me-1"></i> Force Stop
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>

            <div class="col-lg-7 col-xl-8">
                <div class="terminal-box h-100 d-flex flex-column">
                    <div class="terminal-header">
                        <span><i class="bi bi-terminal-fill me-2"></i>Live Execution Log</span>
                        <span id="live-badge" class="badge bg-secondary">MENGAMBIL STATUS...</span>
                    </div>
                    <pre id="logOutput" class="terminal-body flex-grow-1">Initializing terminal...</pre>
                </div>
            </div>
        </div>

        <div class="footer-text pb-3">
            <p class="mb-0 opacity-50">PORT: 80 &bull; CORE: <code>{{ worker_name }}</code> &bull; v2.5 Realtime</p>
        </div>
    </div>

    <script>
        function fetchStatus() {
            fetch('/api/status')
                .then(res => res.json())
                .then(data => {
                    const badge = document.getElementById('live-badge');
                    const btnDeploy = document.getElementById('btn-deploy');
                    const btnStop = document.getElementById('btn-stop');
                    
                    if (data.running) {
                        badge.className = 'badge bg-success pulse-badge border border-success text-white';
                        badge.innerHTML = '<i class="bi bi-activity"></i> RUNNING';
                        
                        btnDeploy.disabled = true;
                        btnDeploy.innerHTML = '<i class="bi bi-arrow-repeat spin-animation me-2"></i> Worker Active';
                        btnDeploy.classList.remove('btn-primary-custom');
                        btnDeploy.classList.add('btn-secondary');
                        
                        btnStop.classList.remove('d-none');
                    } else {
                        badge.className = 'badge bg-secondary border border-secondary text-white';
                        badge.innerHTML = '<i class="bi bi-dash-circle"></i> IDLE / STOPPED';
                        
                        btnDeploy.disabled = false;
                        btnDeploy.innerHTML = '<i class="bi bi-rocket-takeoff-fill me-2"></i> Deploy Worker';
                        btnDeploy.classList.add('btn-primary-custom');
                        btnDeploy.classList.remove('btn-secondary');
                        
                        btnStop.classList.add('d-none');
                    }
                })
                .catch(err => console.log('Error fetching status', err));
        }

        function fetchLogs() {
            fetch('/api/logs')
                .then(res => res.json())
                .then(data => {
                    const logEl = document.getElementById('logOutput');
                    // Cek apakah scroll sudah berada di posisi paling bawah sebelum update
                    const isScrolledToBottom = logEl.scrollHeight - logEl.clientHeight <= logEl.scrollTop + 10;
                    
                    logEl.textContent = data.log || '';
                    
                    // Auto-scroll kebawah jika user tidak sedang ngescroll manual keatas
                    if (isScrolledToBottom) {
                        logEl.scrollTop = logEl.scrollHeight;
                    }
                })
                .catch(err => console.log('Error fetching logs', err));
        }

        function forceStop() {
            if(confirm("Yakin ingin menghentikan script yang sedang berjalan? Proses Chrome mungkin tidak ter-close sempurna.")) {
                fetch('/api/stop', {method: 'POST'})
                    .then(res => res.json())
                    .then(data => {
                        alert(data.message);
                        fetchStatus();
                    });
            }
        }

        // Jalankan polling setiap 2 detik
        setInterval(() => {
            fetchStatus();
            fetchLogs();
        }, 2000);
        
        // Initial Fetch
        fetchStatus();
        fetchLogs();
    </script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# ================= D E C O R A T O R =================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ================= R O U T I N G =================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == PANEL_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash('Akses Ditolak: Passkey tidak valid.', 'danger')
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        # CEK DOUBLE EKSEKUSI
        if is_worker_running():
            flash('⚠️ Aksi ditolak: Worker GHOST DOT masih berjalan! Tunggu hingga selesai atau gunakan Force Stop.', 'warning')
            return redirect(url_for('index'))

        raw_accounts = request.form.get('accounts', '').strip()
        target_email = request.form.get('target_email', '').strip()
        repo_url = request.form.get('repo_url', '').strip()

        if not raw_accounts or not target_email or not repo_url:
            flash('Parameter tidak lengkap. Harap isi semua kolom.', 'warning')
            return redirect(url_for('index'))

        try:
            formatted_accounts = raw_accounts.replace('\r\n', '\n')
            with open(EMAIL_FILE, 'w') as f:
                f.write(formatted_accounts)
                if not formatted_accounts.endswith('\n'):
                    f.write('\n')

            with open(TARGET_FILE, 'w') as f:
                f.write(target_email)
                
            with open(REPO_FILE, 'w') as f:
                f.write(repo_url)
                
            with open(IDX_FILE, 'w') as f:
                pass 

            if os.path.exists(WORKER_SCRIPT):
                # Buka/Buat file log dengan mode 'w' untuk me-reset log setiap eksekusi baru
                log_file = open(LOG_FILE, 'w')
                
                # FLAG -u (unbuffered) PENTING agar output main.py langsung ter-write ke file tanpa delay
                cmd = f"xvfb-run -a python3 -u {WORKER_SCRIPT}"
                
                # Menggunakan stdout=log_file untuk merekam print
                subprocess.Popen(cmd, shell=True, cwd=BASE_DIR, 
                                 stdout=log_file, stderr=subprocess.STDOUT)
                
                flash(f'Deployment berhasil. Engine mulai berjalan untuk: {target_email}', 'success')
            else:
                flash(f'System Error: {WORKER_SCRIPT} missing.', 'danger')

        except Exception as e:
            flash(f'System Failure: {str(e)}', 'danger')
        
        return redirect(url_for('index'))

    current_accounts = ""
    current_target = ""
    current_repo = ""

    if os.path.exists(EMAIL_FILE):
        with open(EMAIL_FILE, 'r') as f:
            current_accounts = f.read().strip()
    
    if os.path.exists(TARGET_FILE):
        with open(TARGET_FILE, 'r') as f:
            current_target = f.read().strip()
            
    if os.path.exists(REPO_FILE):
        with open(REPO_FILE, 'r') as f:
            current_repo = f.read().strip()

    return render_template_string(HTML_TEMPLATE, 
                                  current_accounts=current_accounts, 
                                  current_target=current_target,
                                  current_repo=current_repo,
                                  worker_name="main.py")

# ================= API ENDPOINTS (AJAX) =================

@app.route('/api/status')
@login_required
def get_status():
    """Endpoint untuk AJAX cek status worker"""
    return jsonify({"running": is_worker_running()})

@app.route('/api/logs')
@login_required
def get_logs():
    """Endpoint untuk AJAX menarik isi file log"""
    if not os.path.exists(LOG_FILE):
        return jsonify({"log": "> SYSTEM IDLE.\n> Menunggu instruksi deployment..."})
    
    try:
        with open(LOG_FILE, 'r') as f:
            # Mengambil maksimal 200 baris terakhir agar tidak membuat memori browser penuh
            lines = f.readlines()
            log_content = "".join(lines[-200:]) if lines else "> Log aktif, menunggu inisialisasi module..."
            return jsonify({"log": log_content})
    except Exception as e:
        return jsonify({"log": f"Error membaca log: {str(e)}"})

@app.route('/api/stop', methods=['POST'])
@login_required
def stop_worker():
    """Endpoint untuk Force Stop process"""
    os.system(f"pkill -f '{WORKER_SCRIPT}'")
    return jsonify({"message": "✅ Sinyal terminasi paksa dikirim ke worker."})

# ================= M A I N =================
if __name__ == '__main__':
    print("🚀 GHOST DOT Panel System Initialized on Port 2004...")
    # Menonaktifkan logging Flask default agar terminal server tetap bersih
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    app.run(host='0.0.0.0', port=2004)
