import csv
import io
from datetime import datetime, timezone
from typing import Dict, List, Optional


def fetch_decryptable_credentials(c, cipher: Optional[object]) -> List[Dict[str, str]]:
    if cipher is None:
        return []

    c.execute("SELECT site, username, password FROM credentials")
    rows = c.fetchall()

    items: List[Dict[str, str]] = []
    for site, username, encrypted_password in rows:
        try:
            password = cipher.decrypt(encrypted_password).decode()
            items.append({"site": site, "username": username, "password": password})
        except Exception:
            continue
    return items


def serialize_export_json(items: List[Dict[str, str]]) -> str:
    import json

    payload = {
        "version": 1,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "items": items,
    }
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)


def serialize_export_csv(items: List[Dict[str, str]]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(["site", "username", "password"])
    for item in items:
        writer.writerow([item.get("site", ""), item.get("username", ""), item.get("password", "")])
    return buffer.getvalue()