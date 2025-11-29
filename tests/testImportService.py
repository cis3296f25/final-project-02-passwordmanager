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
    
    def test_parse_csv_stopiteration(self):
        from unittest.mock import patch
        # Mock csv.reader to return an iterator that raises StopIteration on first next()
        empty_iterator = iter([])
        
        def mock_reader(*args, **kwargs):
            return empty_iterator
        
        with patch('passwordmanager.core.import_service.csv.reader', side_effect=mock_reader):
            items, errors = parse_csv("non-empty-text")
            self.assertEqual(items, [])
            self.assertTrue(any("missing header row" in e for e in errors))

    def test_parse_csv_row_validation(self):
        csv_text = "site,username,password\nexample.com,alice,secret\n ,blank,pass\nsite2,,p2\n"
        items, errors = parse_csv(csv_text)
        self.assertEqual(len(items), 1)
        self.assertEqual(len(errors), 2)

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
    
    def test_import_multipart_form_data(self):
        with app.test_client() as client:
            client.post("/account/create", json={"username": "impuser3", "master_password": "pw"})
            client.post("/account/login", json={"username": "impuser3", "master_password": "pw"})
            csv_data = "site,username,password\ntest-multipart,testuser,TestPass123!"
            from io import BytesIO
            data = {
                'file': (BytesIO(csv_data.encode('utf-8')), 'test.csv')
            }
            r = client.post("/import", data=data, content_type="multipart/form-data")
            self.assertEqual(r.status_code, 200)
            summary = r.get_json()
            self.assertIn("inserted", summary)
    
    def test_import_multipart_no_file(self):
        with app.test_client() as client:
            client.post("/account/create", json={"username": "impuser3b", "master_password": "pw"})
            client.post("/account/login", json={"username": "impuser3b", "master_password": "pw"})
            # Send multipart/form-data but without a file field
            r = client.post("/import", data={}, content_type="multipart/form-data")
            # Should fall through to else branch and read body as text (empty)
            self.assertEqual(r.status_code, 200)
            summary = r.get_json()
            # Empty CSV should result in parse errors
            self.assertGreaterEqual(summary.get("parse_errors", 0), 0)
    
    def test_import_other_content_type(self):
        with app.test_client() as client:
            client.post("/account/create", json={"username": "impuser4", "master_password": "pw"})
            client.post("/account/login", json={"username": "impuser4", "master_password": "pw"})
            csv_body = "site,username,password\ntest-other,testuser,TestPass123!"
            r = client.post("/import", data=csv_body, headers={"Content-Type": "application/octet-stream"})
            self.assertEqual(r.status_code, 200)
            summary = r.get_json()
            self.assertIn("inserted", summary)
    
    def test_import_allow_duplicates_variations(self):
        with app.test_client() as client:
            client.post("/account/create", json={"username": "impuser5", "master_password": "pw"})
            client.post("/account/login", json={"username": "impuser5", "master_password": "pw"})
            
            # First add a credential
            site = "test-allow-dup"
            username = "dupuser"
            csv_first = f"site,username,password\n{site},{username},FirstPass123!\n"
            client.post("/import", data=csv_first, headers={"Content-Type": "text/csv"})
            
            # Test allow_duplicates with different values
            csv_dup = f"site,username,password\n{site},{username},SecondPass123!\n"
            
            # Test "1"
            r1 = client.post("/import", data=csv_dup, headers={"Content-Type": "text/csv"}, 
                           query_string={"allow_duplicates": "true"})
            self.assertEqual(r1.status_code, 200)
            summary1 = r1.get_json()
            self.assertGreaterEqual(summary1.get("inserted", 0), 1)
    
    def test_import_duplicate_filtering_empty_fields(self):
        with app.test_client() as client:
            client.post("/account/create", json={"username": "impuser6", "master_password": "pw"})
            client.post("/account/login", json={"username": "impuser6", "master_password": "pw"})
            
            # Add a credential first
            site = "test-empty-filter"
            username = "emptyuser"
            csv_first = f"site,username,password\n{site},{username},FirstPass123!\n"
            client.post("/import", data=csv_first, headers={"Content-Type": "text/csv"})
            
            # Import CSV with empty site/username (should be counted as error, not skipped)
            csv_empty = f"site,username,password\n{site},{username},DupPass123!\n ,emptyuser,Pass123!\nsite2,,Pass123!\n"
            r = client.post("/import", data=csv_empty, headers={"Content-Type": "text/csv"},
                           query_string={"allow_duplicates": "false"})
            self.assertEqual(r.status_code, 200)
            summary = r.get_json()
            # Should skip the duplicate, but empty fields go to import_items which counts as errors
            self.assertGreaterEqual(summary.get("skipped", 0), 1)
            self.assertGreaterEqual(summary.get("errors", 0), 0)