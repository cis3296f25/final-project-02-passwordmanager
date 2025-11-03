import sqlite3
from flask import Flask, request, jsonify
from cryptography.fernet import Fernet
import secrets
import os

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
conn.commit()
###################################################################################

# Flask API
app = Flask(__name__)
vault_locked = False

# POST methods ###########################################################################
@app.route("/lock", methods=["POST"])
def lock_vault():
    """Lock the vault (no add/get/delete allowed until unlocked)."""
    global vault_locked
    vault_locked = True
    return jsonify({"status": "vault locked"})

@app.route("/unlock", methods=["POST"])
def unlock_vault():
    """Unlock the vault."""
    global vault_locked
    vault_locked = False
    return jsonify({"status": "vault unlocked"})

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
    return jsonify({"vault_locked": vault_locked})

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

    c.execute("DELETE FROM credentials WHERE site = ?", (site,))
    conn.commit()
    return jsonify({"status": "deleted"})

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