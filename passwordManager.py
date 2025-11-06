import sqlite3
from flask import Flask, request, jsonify
from cryptography.fernet import Fernet
import secrets
import os

# Persistent key
KEY_FILE = "vault.key"

if os.path.exists(KEY_FILE):
    with open(KEY_FILE, "rb") as f:
        key = f.read()
else:
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)

cipher = Fernet(key)

# Setup database
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

# Flask API
app = Flask(__name__)

@app.route("/add", methods=["POST"])
def add_credential():
    data = request.json
    encrypted_password = cipher.encrypt(data["password"].encode())
    c.execute(
        "INSERT INTO credentials (site, username, password) VALUES (?, ?, ?)",
        (data["site"], data["username"], encrypted_password)
    )
    conn.commit()
    return jsonify({"status": "added"})

@app.route("/get/<site>", methods=["GET"])
def get_credential(site):
    c.execute("SELECT username, password FROM credentials WHERE site = ?", (site,))
    row = c.fetchone()
    if row:
        username, encrypted_password = row
        password = cipher.decrypt(encrypted_password).decode()
        return jsonify({"site": site, "username": username, "password": password})
    return jsonify({"error": "not found"})

@app.route("/delete/<site>", methods=["DELETE"])
def delete_credential(site):
    c.execute("SELECT username, password FROM credentials WHERE site = ?", (site,))
    row = c.fetchone()
    if not row: 
        return jsonify({"error": "not found"})
    username, encrypted_password = row
    password = cipher.decrypt(encrypted_password).decode()
    c.execute("DELETE FROM credentials WHERE site = ?", (site,))
    conn.commit()
    return jsonify({"site": site, "username": username, "password": password})

# Password generator
def generate_password(length=12):
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()"
    return ''.join(secrets.choice(chars) for _ in range(length))

# Test and run
if __name__ == "__main__":
    # Example test credential
    test_site = "example.com"
    test_user = "alice"
    test_pass = generate_password()
    print(f"Generated password for {test_user}@{test_site}: {test_pass}")

    with app.test_client() as client:
        client.post("/add", json={"site": test_site, "username": test_user, "password": test_pass})
        client.post("/add", json={"site": "github.com", "username": "markZuck", "password": test_pass})
        res = client.get(f"/get/{test_site}")
        res2 = client.get(f"/get/{'github.com'}")
        print("Retrieved from vault:", res.json, res2.json)

        deleted_resp = client.delete(f"/delete/{test_site}")
        print("Deleted site:", deleted_resp.json)
        
    # Run server
    app.run(port=5000) # Comment just for push