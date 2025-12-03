import json
from flask import Flask, request, jsonify
from cryptography.fernet import Fernet
import secrets
import os
import datetime
import time

from passwordmanager.core.passwordManager import conn, c
from passwordmanager.core.kdf import default_kdf_params, derive_wrap_key
from passwordmanager.core.vmk import generate_vmk, unwrap_vmk, wrap_vmk
from passwordmanager.core.export_service import (
    fetch_decryptable_credentials,
    serialize_export_json,
    serialize_export_csv,
)
from passwordmanager.core.import_service import (
    parse_csv,
    import_items,
)

# Flask API
app = Flask(__name__)
app.debug = False
# Global variables for the vault and current user
vault_locked = True
current_user = None
current_vmk = None
current_vmk_cipher = None

import passwordmanager.core.secure_cleanup

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

    now = datetime.datetime.utcnow()

    encrypted_password = current_vmk_cipher.encrypt(data["password"].encode())
    c.execute(
        "INSERT INTO credentials (site, username, password, created_at) VALUES (?, ?, ?, ?)", 
        (data["site"], data["username"], encrypted_password, now)       
    )
    new_user_id = c.lastrowid

    conn.commit()

    # format created_at as MM-DD-YYYY for response
    created_at_formatted = now.strftime("%m-%d-%Y")

    return jsonify({"status": "added", "id": new_user_id, "created_at": created_at_formatted}), 201

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

    c.execute("SELECT site, username, password, created_at FROM credentials WHERE id = ?", (cred_id,))
    row = c.fetchone()
    if row:
        site, username, encrypted_password, created_at = row
        password = current_vmk_cipher.decrypt(encrypted_password).decode()

        # Format created_at to MM-DD-YYYY
        created_at_str = None
        if isinstance(created_at, datetime.datetime):
            created_at_str = created_at.strftime("%m-%d-%Y")
        else:
            parsed = datetime.datetime.fromisoformat(str(created_at))
            created_at_str = parsed.strftime("%m-%d-%Y")

        return jsonify({
            "id": cred_id,
            "site": site,
            "username": username,
            "password": password,
            "created_at": created_at_str
        }), 200
    return jsonify({"error": "not found"}), 404

# Password generator
@app.route("/get/generated-password", methods=["GET"])
def generate_password(length=16):
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()"
    password = ''.join(secrets.choice(chars) for _ in range(length))
    return jsonify({"password": password})

# Export endpoint
@app.route("/export", methods=["GET"])
def export_credentials():
    global vault_locked, current_vmk_cipher
    if vault_locked:
        return jsonify({"error": "Vault is locked"}), 423
    if current_vmk_cipher is None:
        return jsonify({"error": "Not logged in"}), 401

    fmt = (request.args.get("format") or "json").lower()
    items = fetch_decryptable_credentials(c, current_vmk_cipher)

    if fmt == "csv":
        csv_text = serialize_export_csv(items)
        filename = f"passwords-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"
        resp = app.response_class(csv_text, mimetype="text/csv")
        resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        return resp

    # default JSON
    from datetime import timezone
    payload = {
        "version": 1,
        "exported_at": datetime.datetime.now(timezone.utc).isoformat(),
        "items": items,
    }
    return jsonify(payload)

# Import endpoint (CSV)
@app.route("/import", methods=["POST"])
def import_credentials():
    global vault_locked, current_vmk_cipher
    if vault_locked:
        return jsonify({"error": "Vault is locked"}), 423
    if current_vmk_cipher is None:
        return jsonify({"error": "Not logged in"}), 401

    csv_text = ""
    content_type = request.content_type or ""
    if content_type.startswith("text/csv"):
        csv_text = request.get_data(as_text=True) or ""
    elif content_type.startswith("multipart/form-data"):
        uploaded = request.files.get("file")
        if uploaded:
            csv_text = uploaded.stream.read().decode("utf-8", errors="replace")
    else:
        # Try to read body as text regardless
        csv_text = request.get_data(as_text=True) or ""

    items, parse_errors = parse_csv(csv_text)
    if any(err.startswith("missing required header") for err in parse_errors):
        return jsonify({"error": "missing required columns", "details": parse_errors}), 400

    # Duplicate policy from query param
    allow_param = (request.args.get("allow_duplicates") or "").strip().lower()
    allow_duplicates = allow_param in ("1", "true", "yes", "y")

    # If not allowing duplicates, pre-filter duplicates and count as skipped
    skipped = 0
    items_to_insert = []
    if not allow_duplicates:
        for it in items:
            site = (it.get("site") or "").strip()
            username = (it.get("username") or "").strip()
            c.execute("SELECT 1 FROM credentials WHERE site = ? AND username = ?", (site, username))
            if c.fetchone():
                skipped += 1
                continue
            items_to_insert.append(it)
    else:
        items_to_insert = items

    summary = import_items(c, items_to_insert, current_vmk_cipher)
    summary["skipped"] = summary.get("skipped", 0) + skipped
    # commit on success/partial success
    conn.commit()
    summary["parse_errors"] = len(parse_errors)
    return jsonify(summary), 200

# List all stored credentials
@app.route("/list", methods=["GET"])
def list_credentials():
    global vault_locked, current_vmk_cipher
    if vault_locked:
        return jsonify({"error": "Vault is locked"}), 423
    if current_vmk_cipher is None:
        return jsonify({"error": "Not logged in"}), 401
    
    c.execute("SELECT id, site, username, password, created_at FROM credentials")
    rows = c.fetchall()

    credentials_list = []
    for cred_id, site, username, encrypted_password, created_at in rows:
        try:
            password = current_vmk_cipher.decrypt(encrypted_password).decode()

            # normalize created_at to MM-DD-YYYY
            created_at_str = None
            if isinstance(created_at, datetime.datetime):
                created_at_str = created_at.strftime("%m-%d-%Y")
            else:
                try:
                    parsed = datetime.datetime.fromisoformat(str(created_at))
                    created_at_str = parsed.strftime("%m-%d-%Y")
                except Exception:
                    created_at_str = str(created_at) if created_at else None

            credentials_list.append({
                "id": cred_id,
                "site": site,
                "username": username,
                "password": password,
                "created_at": created_at_str   
            })
        except Exception:
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
        return jsonify({"error": "not found"}), 404
    
    site, username, encrypted_password = row
    password = current_vmk_cipher.decrypt(encrypted_password).decode()
    c.execute("DELETE FROM credentials WHERE id = ?", (cred_id,))
    conn.commit()
    return jsonify({"id": cred_id, "site": site, "username": username, "password": password})

# PUT methods #########################################################################
# Update password for a credential
@app.route("/update", methods=["PUT"])
def update_credential():
    global vault_locked, current_vmk_cipher
    if vault_locked:
        return jsonify({"error": "Vault is locked"}), 423
    if current_vmk_cipher is None:
        return jsonify({"error": "Not logged in"}), 401
    data = request.json

    cred_id = data.get("id")
    if cred_id is None:
        return jsonify({"error": "missing id"}), 400
    username = data["username"]
    site = data["site"]
    encrypted_password = current_vmk_cipher.encrypt(data["password"].encode())
    c.execute(
        "UPDATE credentials SET site = ?, username = ?, password = ? WHERE id = ?",
        (site, username, encrypted_password, cred_id)
    )

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

    current_time = time.time()
    
    c.execute(
        "SELECT failed_attempts, lockout_until_timestamp FROM login_lockout WHERE id = 1"
    )
    lockout_row = c.fetchone()
    
    if lockout_row:
        failed_attempts, lockout_until = lockout_row
        if lockout_until is not None and current_time < lockout_until:
            remaining_seconds = int(lockout_until - current_time)
            return jsonify({"error": "login locked", "lockout_seconds": remaining_seconds}), 423
    
    c.execute(
        "SELECT wrapped_vmk, salt, kdf, kdf_params FROM user_metadata WHERE username = ?",
        (username,),
    )
    row = c.fetchone()
    if not row:
        _record_failed_attempt()
        return jsonify({"error": "incorrect credentials"}), 401

    wrapped_vmk, salt, kdf_name, kdf_params_json = row
    try:
        params = json.loads(kdf_params_json)
        wrap_key = derive_wrap_key(master_password, salt, params)
        vmk = unwrap_vmk(wrap_key, wrapped_vmk)
    except Exception:
        _record_failed_attempt()
        return jsonify({"error": "incorrect credentials"}), 401

    _reset_lockout()
    global vault_locked, current_user, current_vmk, current_vmk_cipher
    vault_locked = False
    current_user = username
    current_vmk = vmk
    current_vmk_cipher = Fernet(vmk)
    return jsonify({"status": "logged in"})


@app.route("/account/logout", methods=["POST"])
def account_logout():
    return lock_vault()

@app.route("/account/lockout-status", methods=["GET"])
def account_lockout_status():
    current_time = time.time()
    c.execute(
        "SELECT lockout_until_timestamp FROM login_lockout WHERE id = 1"
    )
    lockout_row = c.fetchone()
    
    if not lockout_row or lockout_row[0] is None:
        return jsonify({"locked": False, "lockout_seconds": 0})
    
    lockout_until = lockout_row[0]
    if current_time >= lockout_until:
        return jsonify({"locked": False, "lockout_seconds": 0})
    
    remaining_seconds = int(lockout_until - current_time)
    return jsonify({"locked": True, "lockout_seconds": remaining_seconds})

def _record_failed_attempt():
    current_time = time.time()
    c.execute(
        "SELECT failed_attempts, lockout_until_timestamp FROM login_lockout WHERE id = 1"
    )
    row = c.fetchone()
    
    if row:
        failed_attempts, lockout_until = row
        if lockout_until is not None and current_time < lockout_until:
            return
        
        failed_attempts = (failed_attempts or 0) + 1
    else:
        failed_attempts = 1
    
    if failed_attempts >= 3:
        base_lockout = 15
        lockout_multiplier = 2 ** (failed_attempts - 3)
        lockout_duration = base_lockout * lockout_multiplier
        lockout_until = current_time + lockout_duration
    else:
        lockout_until = None
    
    c.execute(
        """
        INSERT INTO login_lockout (id, failed_attempts, lockout_until_timestamp)
        VALUES (1, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            failed_attempts = ?,
            lockout_until_timestamp = ?
        """,
        (failed_attempts, lockout_until, failed_attempts, lockout_until),
    )
    conn.commit()

def _reset_lockout():
    c.execute("DELETE FROM login_lockout WHERE id = 1")
    conn.commit()

# changes a users master password assuming they're already logged in.
#
# this currently does NOT require any validation of their existing password and 
# should be expanded on in the future
@app.route("/account/password", methods=["PUT"])
def change_master_password():
    global vault_locked, current_user, current_vmk

    if vault_locked or not current_user:
        return jsonify({"error": "not logged in"}), 401

    data = request.json or {}
    new_password = data.get("new_password")
    if not new_password:
        return jsonify({"error": "missing fields"}), 400

    # load user kdf metadata
    c.execute(
        "SELECT salt, kdf_params FROM user_metadata WHERE username = ?",
        (current_user,),
    )
    row = c.fetchone()
    if not row:
        return jsonify({"error": "user not found"}), 404

    salt, kdf_params_json = row
    params = json.loads(kdf_params_json)

    new_wrap_key = derive_wrap_key(new_password, salt, params)

    # rewrap the existing vmk from the last login 
    new_wrapped_vmk = wrap_vmk(new_wrap_key, current_vmk)

    # store 
    c.execute(
        "UPDATE user_metadata SET wrapped_vmk = ? WHERE username = ?",
        (new_wrapped_vmk, current_user),
    )
    conn.commit()

    return jsonify({"status": "password updated"})

@app.route("/check-duplicate", methods=["POST"])
def check_duplicate():

    global vault_locked

    if vault_locked:
        return jsonify({"error": "Vault is locked"}), 423


    data = request.json
    site = data.get("site")
    username = data.get("username")

    c.execute("SELECT 1 FROM credentials WHERE site = ? AND username = ?", (site, username))
    row = c.fetchone()

    # return true if row found, false otherwise
    return jsonify({"exists": bool(row)})


# Test and run
if __name__ == "__main__":
    # Run server
    app.run(port=5000)
