import json
import sqlite3
from flask import Flask, request, jsonify
from cryptography.fernet import Fernet
import secrets
import os

from kdf import default_kdf_params, derive_wrap_key
from vmk import generate_vmk, unwrap_vmk, wrap_vmk

# Database stuff (to be refactored into repository later) #################################
conn = sqlite3.connect("vault.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site TEXT,
    username TEXT,
    password BLOB
)
""")
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

# this is optional, but here for completeness
# it addresses the case where the credentials table was created earlier before we had the id column
# it's also aggressively simple: we create a new table with the id field, copy all the data from the old table into the new, drop the old table, and rename the new table to the old table name
def ensure_credentials_id_column():
    c.execute("PRAGMA table_info(credentials)")
    cols = [row[1] for row in c.fetchall()]
    if "id" not in cols:
        c.execute("""
        CREATE TABLE credentials_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site TEXT,
            username TEXT,
            password BLOB
        )
        """)
        c.execute("""
        INSERT INTO credentials_new (site, username, password)
        SELECT site, username, password FROM credentials
        """)
        c.execute("DROP TABLE credentials")
        c.execute("ALTER TABLE credentials_new RENAME TO credentials")
        conn.commit()

ensure_credentials_id_column()

# Flask API
app = Flask(__name__)
app.debug = False
# Global variables for the vault and current user
vault_locked = True
current_user = None
current_vmk_cipher = None

# POST methods ###########################################################################
@app.route("/lock", methods=["POST"])
def lock_vault():
    """Lock the vault (no add/get/delete allowed until unlocked)."""
    global vault_locked, current_user, current_vmk_cipher
    vault_locked = True
    current_user = None
    current_vmk_cipher = None
    return jsonify({"status": "vault locked"})

@app.route("/unlock", methods=["POST"])
def unlock_vault():
    """Unlock the vault."""
    global vault_locked
    vault_locked = False
    return jsonify({"status": "vault unlocked"})

@app.route("/add", methods=["POST"])
def add_credential():
    global vault_locked, current_vmk_cipher
    if vault_locked:
        return jsonify({"error": "Vault is locked"}), 423
    if current_vmk_cipher is None:
        return jsonify({"error": "Not logged in"}), 401

    data = request.json
    encrypted_password = current_vmk_cipher.encrypt(data["password"].encode())
    c.execute(
        "INSERT INTO credentials (site, username, password) VALUES (?, ?, ?)",
        (data["site"], data["username"], encrypted_password)
    )
    conn.commit()
    return jsonify({"status": "added"}), 201

# GET methods ###########################################################################
@app.route("/status", methods=["GET"])
def vault_status():
    """Check current vault state."""
    return jsonify({"vault_locked": vault_locked})

@app.route("/get/<int:cred_id>", methods=["GET"])
def get_credential(cred_id):
    global vault_locked, current_vmk_cipher
    if vault_locked:
        return jsonify({"error": "Vault is locked"}), 423
    if current_vmk_cipher is None:
        return jsonify({"error": "Not logged in"}), 401

    c.execute("SELECT site, username, password FROM credentials WHERE id = ?", (cred_id,))
    row = c.fetchone()
    if row:
        site, username, encrypted_password = row
        password = current_vmk_cipher.decrypt(encrypted_password).decode()
        return jsonify({"id": cred_id, "site": site, "username": username, "password": password}), 409
    return jsonify({"error": "not found"}), 404

# Password generator
@app.route("/get/generated-password", methods=["GET"])
def generate_password(length=12):
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()"
    password = ''.join(secrets.choice(chars) for _ in range(length))
    return jsonify({"password": password})

# List all stored credentials
@app.route("/list", methods=["GET"])
def list_credentials():
    global vault_locked, current_vmk_cipher
    if vault_locked:
        return jsonify({"error": "Vault is locked"}), 423
    if current_vmk_cipher is None:
        return jsonify({"error": "Not logged in"}), 401
    
    # selects all columns
    c.execute("SELECT id, site, username, password FROM credentials")
    rows = c.fetchall()

    credentials_list = []
    for cred_id, site, username, encrypted_password in rows:
        try:
            # decrypt pw for display
            password = current_vmk_cipher.decrypt(encrypted_password).decode()
            credentials_list.append({"id": cred_id, "site": site, "username": username, "password": password})
        except Exception:
            # hide entries that are not decryptable by the current user
            continue
    return jsonify(credentials_list)


# DELETE methods #############################################################################
@app.route("/delete/<int:cred_id>", methods=["DELETE"])
def delete_credential(cred_id):
    global vault_locked, current_vmk_cipher
    if vault_locked:
        return jsonify({"error": "Vault is locked"}), 423
    if current_vmk_cipher is None:
        return jsonify({"error": "Not logged in"}), 401
    
    c.execute("SELECT site, username, password FROM credentials WHERE id = ?", (cred_id,))
    row = c.fetchone()
    if not row:
        return jsonify({"error": "not found"})
    
    site, username, encrypted_password = row
    password = current_vmk_cipher.decrypt(encrypted_password).decode()
    c.execute("DELETE FROM credentials WHERE id = ?", (cred_id,))
    conn.commit()
    return jsonify({"id": cred_id, "site": site, "username": username, "password": password})

# PUT methods #########################################################################
# Update password for a site
@app.route("/update", methods=["PUT"])
def update_password():
    global vault_locked, current_vmk_cipher
    if vault_locked:
        return jsonify({"error": "Vault is locked"}), 423
    if current_vmk_cipher is None:
        return jsonify({"error": "Not logged in"}), 401
    data = request.json
    cred_id = data.get("id")
    if cred_id is None:
        return jsonify({"error": "missing id"}), 400
    encrypted_password = current_vmk_cipher.encrypt(data["password"].encode())
    c.execute("UPDATE credentials SET password = ? WHERE id = ?", (encrypted_password, cred_id))
    conn.commit()
    return jsonify({"status": "updated", "id": cred_id})

# Account methods ######################################################################
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
        return jsonify({"error": "incorrect credentials"}), 401

    wrapped_vmk, salt, kdf_name, kdf_params_json = row
    try:
        params = json.loads(kdf_params_json)
        wrap_key = derive_wrap_key(master_password, salt, params)
        vmk = unwrap_vmk(wrap_key, wrapped_vmk)
    except Exception:
        return jsonify({"error": "incorrect credentials"}), 401

    global vault_locked, current_user, current_vmk_cipher
    vault_locked = False
    current_user = username
    current_vmk_cipher = Fernet(vmk)
    return jsonify({"status": "logged in"})


@app.route("/account/logout", methods=["POST"])
def account_logout():
    return lock_vault()

# Test and run
if __name__ == "__main__":
    # Example test credential
    test_site = "example.com"
    test_user = "alice"
    test_pass = "testpassword"
    print(f"Generated password for {test_user}@{test_site}: {test_pass}")

    with app.test_client() as client:
        create_resp = client.post("/account/create", json={"username": "test", "master_password": "test"})
        print("/account/create:", create_resp.status_code, create_resp.json)
        login_resp = client.post("/account/login", json={"username": "test", "master_password": "test"})
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