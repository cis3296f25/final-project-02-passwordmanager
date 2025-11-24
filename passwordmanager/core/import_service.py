import csv
import io
from typing import Dict, List, Tuple, Optional


RequiredHeaders = ("site", "username", "password")


def _normalize_headers(headers: List[str]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for h in headers:
        key = h.strip().lower().replace("_", "").replace("-", "")
        mapping[key] = h
    return mapping


def parse_csv(text: str) -> Tuple[List[Dict[str, str]], List[str]]:
    items: List[Dict[str, str]] = []
    errors: List[str] = []

    if not text:
        errors.append("empty file")
        return items, errors

    buffer = io.StringIO(text)
    reader = csv.reader(buffer)
    try:
        headers = next(reader)
    except StopIteration:
        errors.append("missing header row")
        return items, errors

    header_map = _normalize_headers(headers)

    required_keys = {}
    for req in RequiredHeaders:
        norm_req = req.lower()
        norm_key = norm_req.replace("_", "").replace("-", "")
        if norm_key not in header_map:
            errors.append(f"missing required header: {req}")
        else:
            required_keys[req] = header_map[norm_key]

    if errors:
        return items, errors

    buffer.seek(0)
    dict_reader = csv.DictReader(buffer)
    row_index = 1
    for row in dict_reader:
        site = (row.get(required_keys["site"]) or "").strip()
        username = (row.get(required_keys["username"]) or "").strip()
        password = (row.get(required_keys["password"]) or "").strip()

        if not site or not username or not password:
            errors.append(f"row {row_index}: missing required fields")
            row_index += 1
            continue

        items.append({"site": site, "username": username, "password": password})
        row_index += 1

    return items, errors


def import_items(
    c,
    items: List[Dict[str, str]],
    current_vmk_cipher: Optional[object],
) -> Dict[str, int]:
    inserted = 0
    skipped = 0
    errors = 0

    if current_vmk_cipher is None:
        return {"inserted": 0, "skipped": 0, "errors": len(items)}

    for item in items:
        site = (item.get("site") or "").strip()
        username = (item.get("username") or "").strip()
        password = item.get("password")
        if not site or not username or password is None:
            errors += 1
            continue

        try:
            encrypted_password = current_vmk_cipher.encrypt(password.encode("utf-8"))
            c.execute(
                "INSERT INTO credentials (site, username, password) VALUES (?, ?, ?)",
                (site, username, encrypted_password),
            )
            inserted += 1
        except Exception:
            errors += 1

    return {"inserted": inserted, "skipped": skipped, "errors": errors}