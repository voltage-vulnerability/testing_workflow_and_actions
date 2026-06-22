import os
import sqlite3
import hashlib
import requests
import subprocess
from flask import Flask, request, render_template_string, make_response

app = Flask(__name__)

# ❌ ISSUE 1: Hardcoded sensitive credentials & API keys
ADMIN_DB_PASSWORD = "p@ssword!_99831_secure_prod"
AWS_SECRET_ACCESS_KEY = "AKIAUHBNDFXZ7R6QKL2M/vN72bXmKqP9zRt5wLc1v"

# ❌ ISSUE 2: Weak cryptographic hashing algorithm (MD5)
def hash_user_password(password):
    hasher = hashlib.md5()
    hasher.update(password.encode('utf-8'))
    return hasher.hexdigest()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # ❌ ISSUE 3: SQL Injection (SQLi)
    query = f"SELECT id, role FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    user = cursor.fetchone()
    
    if user:
        # ❌ ISSUE 4: Broken/Insecure Session Management
        # Setting a plaintext, guessable user ID cookie without HttpOnly or Secure flags
        response = make_response("Welcome back!")
        response.set_cookie('user_session', value=str(user[0]), secure=False, httponly=False)
        return response
    return "Invalid credentials", 401

@app.route('/api/v1/invoice', methods=['GET'])
def get_invoice():
    # ❌ ISSUE 5: BOLA / Broken Access Control (IDOR)
    # Fetching an invoice using a raw user-supplied ID directly from the URL query parameter 
    # without checking if the currently logged-in session user actually owns this invoice.
    invoice_id = request.args.get('id')
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT file_path FROM invoices WHERE id = {invoice_id}")
    invoice = cursor.fetchone()
    return f"Displaying invoice data: {invoice[0]}"

@app.route('/update-email', methods=['POST'])
def update_email():
    # ❌ ISSUE 6: Cross-Site Request Forgery (CSRF)
    # State-changing action executed over an API without validating an anti-CSRF token payload
    session_id = request.cookies.get('user_session')
    new_email = request.form.get('email')
    
    if session_id:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute(f"UPDATE users SET email = '{new_email}' WHERE id = {session_id}")
        conn.commit()
        return "Email updated successfully!"
    return "Unauthorized", 403

@app.route('/fetch-avatar', methods=['GET'])
def fetch_avatar_from_url():
    # ❌ ISSUE 7: Server-Side Request Forgery (SSRF)
    # The server accepts an arbitrary URL parameter and fetches internal network files or cloud metadata
    image_url = request.args.get('url')
    
    # An attacker can pass 'http://169.254.169' to steal AWS instance tokens
    fetched_data = requests.get(image_url, timeout=5)
    return make_response(fetched_data.content)

@app.route('/ping', methods=['GET'])
def network_ping():
    target_host = request.args.get('host')
    # ❌ ISSUE 8: Command Injection (Remote Code Execution)
    command = f"ping -c 1 {target_host}"
    output = subprocess.check_output(command, shell=True)
    return f"<pre>{output.decode('utf-8')}</pre>"

@app.route('/profile', methods=['GET'])
def view_profile():
    user_bio = request.args.get('bio', '')
    # ❌ ISSUE 9: Cross-Site Scripting (XSS)
    html_template = f"<html><body><p>User Biography: {user_bio}</p></body></html>"
    return render_template_string(html_template)

@app.route('/debug-logs', methods=['GET'])
def read_log_file():
    log_path = request.args.get('file')
    # ❌ ISSUE 10: Path Traversal (Local File Inclusion)
    base_dir = "/var/log/app/"
    full_path = os.path.join(base_dir, log_path)
    with open(full_path, 'r') as file:
        content = file.read()
    return f"<pre>{content}</pre>"

# ❌ ISSUE 11: Insecure Debug Mode Enabled in Production
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
