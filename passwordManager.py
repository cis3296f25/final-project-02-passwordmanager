import sqlite3
from flask import Flask, request, jsonify
from cryptography.fernet import Fernet
import secrets
import os
import json
from kdf import derive_wrap_key, default_kdf_params
from vmk import generate_vmk, wrap_vmk, unwrap_vmk

# Database stuff (to be refactored into repository later) #################################
KEY_FILE = "vault.key"

if os.path.exists(KEY_FILE):
    with open(KEY_FILE, "rb") as f:
        key = f.read()
else:
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)

cipher = Fernet(key)

conn = sqlite3.connect("vault.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS credentials (
    site TEXT,
    username TEXT,
    password BLOB
)
""")
## New: user metadata to support per-user VMK wrapping
c.execute("""
CREATE TABLE IF NOT EXISTS user_metadata (
    username TEXT PRIMARY KEY,
    wrapped_vmk BLOB NOT NULL,
    salt BLOB NOT NULL,
    kdf TEXT NOT NULL,
    kdf_params TEXT NOT NULL
)
""")
conn.commit()
###################################################################################

# Flask API
app = Flask(__name__)
app.debug = False
# Locked until a successful login
vault_locked = True
current_user = None
# Keeping this for now pending testing
current_vmk_cipher = None  # Fernet instance constructed with decrypted VMK for the session

# POST methods ###########################################################################
@app.route("/lock", methods=["POST"])
def lock_vault():
    """Lock the vault (no add/get/delete allowed until unlocked)."""
    global vault_locked
    vault_locked = True
    # Clear session state
    global current_user, current_vmk_cipher
    current_user = None
    current_vmk_cipher = None
    return jsonify({"status": "vault locked"})

@app.route("/unlock", methods=["POST"])
def unlock_vault():
    """Unlock the vault."""
    global vault_locked
    # For backward-compat, allow manual unlock (not recommended). Prefer /account/login.
    vault_locked = False
    return jsonify({"status": "vault unlocked (no user session)"})


# Account endpoints ######################################################################
@app.route("/account/create", methods=["POST"])
def create_account():
    data = request.json or {}
    username = data.get("username")
    master_password = data.get("master_password")
    if not username or not master_password:
        return jsonify({"error": "missing fields"}), 400

    # Prevent duplicate usernames
    c.execute("SELECT 1 FROM user_metadata WHERE username = ?", (username,))
    if c.fetchone():
        return jsonify({"error": "username already exists"}), 409

    salt = os.urandom(16)
    kdf_params = default_kdf_params()
    wrap_key = derive_wrap_key(master_password, salt, kdf_params)

    vmk = generate_vmk()
    wrapped_vmk = wrap_vmk(wrap_key, vmk)

    c.execute(
        """
        INSERT INTO user_metadata (username, wrapped_vmk, salt, kdf, kdf_params)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            username,
            wrapped_vmk,
            salt,
            "argon2id",
            json.dumps(kdf_params),
        ),
    )
    conn.commit()
    return jsonify({"status": "account created"}), 201


@app.route("/account/login", methods=["POST"])
def account_login():
    data = request.json or {}
    username = data.get("username")
    master_password = data.get("master_password")
    if not username or not master_password:
        return jsonify({"error": "incorrect credentials"}), 401

    c.execute(
        "SELECT wrapped_vmk, salt, kdf, kdf_params FROM user_metadata WHERE username = ?",
        (username,),
    )
    row = c.fetchone()
    if not row:
        # Generic to prevent enumeration
        return jsonify({"error": "incorrect credentials"}), 401

    wrapped_vmk, salt, kdf_name, kdf_params_json = row
    try:
        params = json.loads(kdf_params_json)
        wrap_key = derive_wrap_key(master_password, salt, params)
        vmk = unwrap_vmk(wrap_key, wrapped_vmk)
    except Exception:
        return jsonify({"error": "incorrect credentials"}), 401

    # Establish session
    global vault_locked, current_user, current_vmk_cipher
    vault_locked = False
    current_user = username
    current_vmk_cipher = Fernet(vmk)
    return jsonify({"status": "logged in"})


@app.route("/account/logout", methods=["POST"])
def account_logout():
    # Reuse lock semantics
    return lock_vault()

@app.route("/add", methods=["POST"])
def add_credential():
    global vault_locked
    if vault_locked:
        return jsonify({"error": "Vault is locked"}), 423

    data = request.json
    encrypted_password = cipher.encrypt(data["password"].encode())
    c.execute(
        "INSERT INTO credentials (site, username, password) VALUES (?, ?, ?)",
        (data["site"], data["username"], encrypted_password)
    )
    conn.commit()
    return jsonify({"status": "added"})

# GET methods ###########################################################################
@app.route("/status", methods=["GET"])
def vault_status():
    """Check current vault state."""
    return jsonify({
        "vault_locked": vault_locked,
        "current_user": current_user,
        "session": "active" if (not vault_locked and current_user) else "none",
    })

@app.route("/get/<site>", methods=["GET"])
def get_credential(site):
    global vault_locked
    if vault_locked:
        return jsonify({"error": "Vault is locked"}), 423

    c.execute("SELECT username, password FROM credentials WHERE site = ?", (site,))
    row = c.fetchone()
    if row:
        username, encrypted_password = row
        password = cipher.decrypt(encrypted_password).decode()
        return jsonify({"site": site, "username": username, "password": password})
    return jsonify({"error": "not found"})

# Password generator
@app.route("/get/generated-password", methods=["GET"])
def generate_password(length=12):
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()"
    password = ''.join(secrets.choice(chars) for _ in range(length))
    return jsonify({"password": password})

# List all stored credentials
@app.route("/list", methods=["GET"])
def list_credentials():
    c.execute("SELECT site, username FROM credentials")
    rows = c.fetchall()
    return jsonify([{"site": site, "username": username} for site, username in rows])

# DELETE methods #############################################################################
@app.route("/delete/<site>", methods=["DELETE"])
def delete_credential(site):
    global vault_locked
    if vault_locked:
        return jsonify({"error": "Vault is locked"}), 423
    
    c.execute("SELECT username, password FROM credentials WHERE site = ?", (site,))
    row = c.fetchone()
    if not row:
        return jsonify({"error": "not found"})
    
    username, encrypted_password = row
    password = cipher.decrypt(encrypted_password).decode()
    c.execute("DELETE FROM credentials WHERE site = ?", (site,))
    conn.commit()
    return jsonify({"site": site, "username": username, "password": password})

# PUT methods #########################################################################
# Update password for a site
@app.route("/update", methods=["PUT"])
def update_password():
    data = request.json
    encrypted_password = cipher.encrypt(data["password"].encode())
    c.execute("UPDATE credentials SET password = ? WHERE site = ?", (encrypted_password, data["site"]))
    conn.commit()
    return jsonify({"status": "updated", "site": data["site"]})


# Test and run
if __name__ == "__main__":
    # Example test credential
    test_site = "example.com"
    test_user = "alice"
    test_pass = "testpassword"
    print(f"Generated password for {test_user}@{test_site}: {test_pass}")

    with app.test_client() as client:
        create_resp = client.post("/account/create", json={"username": "demo2", "master_password": "CorrectHorseBatteryStaple"})
        print("/account/create:", create_resp.status_code, create_resp.json)
        login_resp = client.post("/account/login", json={"username": "demo2", "master_password": "CorrectHorseBatteryStaple"})
        print("/account/login:", login_resp.status_code, login_resp.json)

        client.post("/add", json={"site": test_site, "username": test_user, "password": test_pass})
        client.post("/add", json={"site": "github.com", "username": "markZuck", "password": test_pass})
        res = client.get(f"/get/{test_site}")
        res2 = client.get(f"/get/{'github.com'}")
        print("Retrieved from vault:", res.json, res2.json)

        deleted_resp = client.delete(f"/delete/{test_site}")
        print("Deleted site:", deleted_resp.json)

        list_resp = client.get("/list")
        print("All stored credentials:", list_resp.json)

        client.put("/update", json={"site": "github.com", "password": "NewSecurePass123!"})
        updated_resp = client.get("/get/github.com")
        print("Updated GitHub credential:", updated_resp.json)

        
    # Run server
    app.run(port=5000)