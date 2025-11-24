import unittest
import sqlite3

from passwordmanager.core.import_service import parse_csv, import_items
from passwordmanager.api.routes import app

class FakeCipher:
    def encrypt(self, data: bytes) -> bytes:
        return b"enc:" + data

class TestImportService(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.c = self.conn.cursor()
        self.c.execute(
            """
            CREATE TABLE credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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

    def test_parse_csv_success_case_insensitive_headers(self):
        csv_text = "Site,UserName,Password\nexample.com,alice,secret\n"
        items, errors = parse_csv(csv_text)
        self.assertEqual(errors, [])
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["site"], "example.com")
        self.assertEqual(items[0]["username"], "alice")
        self.assertEqual(items[0]["password"], "secret")

    def test_parse_csv_missing_header(self):
        csv_text = "site,username\nexample.com,alice\n"
        items, errors = parse_csv(csv_text)
        self.assertEqual(items, [])
        self.assertTrue(any("missing required header" in e for e in errors))

    def test_parse_csv_empty_file(self):
        items, errors = parse_csv("")
        self.assertEqual(items, [])
        self.assertTrue(any("empty file" in e for e in errors))

    def test_parse_csv_missing_header_row(self):
        items, errors = parse_csv("\n")
        self.assertEqual(items, [])
        self.assertTrue(any("missing header row" in e or "missing required header" in e for e in errors))

    def test_parse_csv_row_validation(self):
        csv_text = "site,username,password\nexample.com,alice,secret\n ,blank,pass\nsite2,,p2\n"
        items, errors = parse_csv(csv_text)
        self.assertEqual(len(items), 1)
        self.assertEqual(len(errors), 2)

    def test_import_items_inserts_and_skips_duplicates(self):
        items = [
            {"site": "ex.com", "username": "u1", "password": "p1"},
            {"site": "ex.com", "username": "u1", "password": "p1-dup"},
            {"site": "ex.com", "username": "u2", "password": "p2"},
        ]
        summary = import_items(self.c, items, FakeCipher())
        self.assertEqual(summary["inserted"], 2)
        self.assertEqual(summary["skipped"], 1)
        self.assertEqual(summary["errors"], 0)
        self.c.execute("SELECT site, username, password FROM credentials ORDER BY username")
        rows = self.c.fetchall()
        self.assertEqual(len(rows), 2)
        self.assertTrue(rows[0][2].startswith(b"enc:"))
        self.assertTrue(rows[1][2].startswith(b"enc:"))

    def test_import_items_reports_errors_when_no_cipher(self):
        items = [{"site": "ex.com", "username": "u1", "password": "p1"}]
        summary = import_items(self.c, items, None)
        self.assertEqual(summary["inserted"], 0)
        self.assertEqual(summary["skipped"], 0)
        self.assertEqual(summary["errors"], 1)

    def test_import_items_password_none_and_encrypt_exception(self):
        class BadCipher:
            def encrypt(self, data: bytes) -> bytes:
                raise RuntimeError("fail")

        items = [
            {"site": "ex.com", "username": "u1", "password": None},
            {"site": "ex.com", "username": "u2", "password": "p2"},
        ]
        summary = import_items(self.c, items, BadCipher())
        self.assertEqual(summary["inserted"], 0)
        self.assertEqual(summary["skipped"], 0)
        self.assertEqual(summary["errors"], 2)

    # ---------- Endpoint tests ----------
    def test_import_locked_423(self):
        with app.test_client() as client:
            client.post("/lock")
            r = client.post("/import", data="site,username,password\ns,u,p\n", headers={"Content-Type": "text/csv"})
            self.assertEqual(r.status_code, 423)

    def test_import_not_logged_in_401(self):
        with app.test_client() as client:
            client.post("/lock")
            client.post("/account/logout")
            client.post("/unlock")
            r = client.post("/import", data="site,username,password\ns,u,p\n", headers={"Content-Type": "text/csv"})
            self.assertEqual(r.status_code, 401)

    def test_import_missing_columns_400(self):
        with app.test_client() as client:
            client.post("/account/create", json={"username": "impuser", "master_password": "pw"})
            client.post("/account/login", json={"username": "impuser", "master_password": "pw"})
            bad_csv = "site,username\ns,u\n"
            r = client.post("/import", data=bad_csv, headers={"Content-Type": "text/csv"})
            self.assertEqual(r.status_code, 400)
            j = r.get_json()
            self.assertIn("missing required columns", j.get("error", ""))

    def test_import_happy_good_path_200(self):
        with app.test_client() as client:
            client.post("/account/create", json={"username": "impuser2", "master_password": "pw"})
            client.post("/account/login", json={"username": "impuser2", "master_password": "pw"})
            csv_body = "site,username,password\nex.com,u1,p1\nex.com,u1,pdup\nex.com,u2,p2\n"
            r = client.post("/import", data=csv_body, headers={"Content-Type": "text/csv"})
            self.assertEqual(r.status_code, 200)
            summary = r.get_json()
            self.assertIn("inserted", summary)
            self.assertIn("skipped", summary)
            lst = client.get("/list")
            self.assertEqual(lst.status_code, 200)
            items = lst.get_json()
            sites = {i.get("site") for i in items}
            self.assertIn("ex.com", sites)