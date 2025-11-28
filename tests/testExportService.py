import unittest
import json
import sqlite3
from datetime import datetime

from passwordmanager.core.export_service import (
    fetch_decryptable_credentials,
    serialize_export_json,
    serialize_export_csv,
)
from passwordmanager.api.routes import app


class FakeCipher:
    def decrypt(self, token: bytes) -> bytes:
        # Return payload for tokens prefixed with b"ok:", else raise to simulate undecryptable
        if token.startswith(b"ok:"):
            return token.split(b"ok:", 1)[1]
        raise ValueError("undecryptable")


class TestExportService(unittest.TestCase):
    def setUp(self):
        # In-memory DB with credentials table
        self.conn = sqlite3.connect(":memory:")
        self.c = self.conn.cursor()
        self.c.execute(
            """
            CREATE TABLE credentials (
                site TEXT,
                username TEXT,
                password BLOB
            )
            """
        )
        self.conn.commit()

    def tearDown(self):
        try:
            self.conn.close()
        except Exception:
            pass

    def test_fetch_returns_empty_when_no_vmk(self):
        # insert a row (should be ignored since no VMK)
        self.c.execute(
            "INSERT INTO credentials (site, username, password) VALUES (?, ?, ?)",
            ("example.com", "alice", b"ok:secret"),
        )
        self.conn.commit()
        items = fetch_decryptable_credentials(self.c, None)
        self.assertEqual(items, [])

    def test_fetch_decryptable_and_skips_undecryptable(self):
        # one decryptable, one not
        self.c.execute(
            "INSERT INTO credentials (site, username, password) VALUES (?, ?, ?)",
            ("example.com", "alice", b"ok:alpha"),
        )
        self.c.execute(
            "INSERT INTO credentials (site, username, password) VALUES (?, ?, ?)",
            ("example.org", "bob", b"bad:beta"),
        )
        self.conn.commit()
        items = fetch_decryptable_credentials(self.c, FakeCipher())
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["site"], "example.com")
        self.assertEqual(items[0]["username"], "alice")
        self.assertEqual(items[0]["password"], "alpha")

    def test_serialize_export_json_structure(self):
        items = [
            {"site": "a.com", "username": "u", "password": "p"},
            {"site": "b.org", "username": "v", "password": "q"},
        ]
        out = serialize_export_json(items)
        data = json.loads(out)
        self.assertEqual(data["version"], 1)
        # exported_at is ISO-8601
        datetime.fromisoformat(data["exported_at"])
        self.assertEqual(data["items"], items)

    def test_serialize_export_json_empty(self):
        out = serialize_export_json([])
        data = json.loads(out)
        self.assertEqual(data["version"], 1)
        self.assertEqual(data["items"], [])

    def test_serialize_export_csv(self):
        items = [
            {"site": "a.com", "username": "u", "password": "p"},
            {"site": "b.org", "username": "v", "password": "q"},
        ]
        csv_text = serialize_export_csv(items)
        lines = [ln for ln in csv_text.splitlines() if ln.strip() != ""]
        self.assertGreaterEqual(len(lines), 3)
        self.assertEqual(lines[0], "site,username,password")
        self.assertIn("a.com,u,p", lines[1])
        self.assertIn("b.org,v,q", lines[2])

    def test_serialize_export_csv_empty(self):
        csv_text = serialize_export_csv([])
        lines = [ln for ln in csv_text.splitlines() if ln.strip() != ""]
        self.assertEqual(lines, ["site,username,password"])

    # ---------- Endpoint tests ----------
    def test_export_locked_423(self):
        with app.test_client() as client:
            client.post("/lock")
            r = client.get("/export")
            self.assertEqual(r.status_code, 423)

    def test_export_not_logged_in_401(self):
        with app.test_client() as client:
            # ensure locked then unlock to test 401 (logout locks)
            client.post("/lock")
            client.post("/account/logout")
            client.post("/unlock")
            r = client.get("/export")
            self.assertEqual(r.status_code, 401)

    def test_export_json_success(self):
        with app.test_client() as client:
            # create+login and add a credential
            client.post("/account/create", json={"username": "expuser", "master_password": "pw"})
            client.post("/account/login", json={"username": "expuser", "master_password": "pw"})
            client.post("/add", json={"site": "sitej", "username": "uj", "password": "pj"})
            r = client.get("/export?format=json")
            self.assertEqual(r.status_code, 200)
            data = json.loads(r.data.decode())
            self.assertEqual(data.get("version"), 1)
            self.assertIsInstance(data.get("items"), list)
            self.assertTrue(any(it.get("site") == "sitej" for it in data["items"]))

    def test_export_csv_success(self):
        with app.test_client() as client:
            client.post("/account/create", json={"username": "expuser2", "master_password": "pw"})
            client.post("/account/login", json={"username": "expuser2", "master_password": "pw"})
            client.post("/add", json={"site": "sitec", "username": "uc", "password": "pc"})
            r = client.get("/export?format=csv")
            self.assertEqual(r.status_code, 200)
            self.assertTrue(r.content_type.startswith("text/csv"))
            text = r.data.decode()
            self.assertIn("site,username,password", text.splitlines()[0])
            self.assertIn("sitec", text)