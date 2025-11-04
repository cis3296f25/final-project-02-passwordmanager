import sqlite3
from flask import Flask, request, jsonify
from cryptography.fernet import Fernet
import secrets
import os
import string
import random

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
    c.execute("DELETE FROM credentials WHERE site = ?", (site,))
    conn.commit()
    return jsonify({"status": "deleted"}), 200

# Password generator
def generate_password(length=12):
    lower = string.ascii_lowercase
    upper = string.ascii_uppercase
    digits = string.digits
    symbols = "!@#$%^&*()"

    if length < 4:
        length = 4

    # Ensure at least one of each category
    required = [
        secrets.choice(lower),
        secrets.choice(upper),
        secrets.choice(digits),
        secrets.choice(symbols),
    ]
    allchars = lower + upper + digits + symbols
    remaining = [secrets.choice(allchars) for _ in range(length - len(required))]
    pw_list = required + remaining
    random.SystemRandom().shuffle(pw_list)
    return "".join(pw_list)

# Run server
if __name__ == "__main__":
    app.run(port=5000)
