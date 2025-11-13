import unittest
import random
import string
import sqlite3
import tempfile
import os
from passwordManager import app, c, conn
import passwordManager as pm

class TestVaultAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()
        # Ensure an account exists and we are logged in
        username = "unittest-user"
        master_password = "unittest-pass"
        resp = cls.client.post("/account/create", json={"username": username, "master_password": master_password})
        # ignore duplicate username error
        cls.client.post("/account/login", json={"username": username, "master_password": master_password})

    def tearDown(self):
        c.execute("DELETE FROM credentials WHERE site LIKE 'unittest-%'")
        conn.commit()

    def test_add_get_delete_roundtrip(self):
        site = "unittest-example.com"
        user = "tester"
        pwd  = "TestPassword"

        r = self.client.post("/add", json={"site": site, "username": user, "password": pwd})
        self.assertEqual(r.status_code, 201)
        new_id = r.get_json().get("id")
        self.assertIsNotNone(new_id)

        r = self.client.get(f"/get/{new_id}")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertEqual(data["id"], new_id)
        self.assertEqual(data["username"], user)
        self.assertEqual(data["password"], pwd)

        # delete returns the deleted record in current API
        r = self.client.delete(f"/delete/{new_id}")
        self.assertEqual(r.status_code, 200)
        j = r.get_json()
        self.assertEqual(j.get("id"), new_id)
        self.assertTrue(j.get("site") == site or j.get("status") == "deleted")

        r = self.client.get(f"/get/{new_id}")
        self.assertEqual(r.get_json().get("error"), "not found")

    def test_per_user_encryption_distinct_ciphertexts(self):
        # two users, same plaintext password (ciphertexts should differ)
        self.client.post("/account/create", json={"username": "user_a", "master_password": "pw_a"})
        self.client.post("/account/create", json={"username": "user_b", "master_password": "pw_b"})

        # login A and add
        self.client.post("/account/login", json={"username": "user_a", "master_password": "pw_a"})
        self.client.post("/add", json={"site": "site_a", "username": "a", "password": "plaintext"})
        # get ciphertext A
        c.execute("SELECT password FROM credentials WHERE site = ?", ("site_a",))
        row_a = c.fetchone()
        self.assertIsNotNone(row_a)
        ciphertext_a = row_a[0]
        self.client.post("/account/logout")

        # login B and add
        self.client.post("/account/login", json={"username": "user_b", "master_password": "pw_b"})
        self.client.post("/add", json={"site": "site_b", "username": "b", "password": "plaintext"})
        # get ciphertext B
        c.execute("SELECT password FROM credentials WHERE site = ?", ("site_b",))
        row_b = c.fetchone()
        self.assertIsNotNone(row_b)
        ciphertext_b = row_b[0]
        self.client.post("/account/logout")

        # ciphertexts should differ because different VMKs
        self.assertNotEqual(ciphertext_a, ciphertext_b)

    def test_list_hides_undecryptable_rows(self):
        # ensure accounts exist (creates if not exist, returns error if exists and we proceed to login)
        self.client.post("/account/create", json={"username": "user_a", "master_password": "pw_a"})
        self.client.post("/account/create", json={"username": "user_b", "master_password": "pw_b"})

        # login as user A and add credential
        self.client.post("/account/login", json={"username": "user_a", "master_password": "pw_a"})
        self.client.post("/add", json={"site": "site", "username": "ua", "password": "secretA"})
        self.client.post("/account/logout")

        # login as user B and list; undecryptable entry should be hidden
        self.client.post("/account/login", json={"username": "user_b", "master_password": "pw_b"})
        resp = self.client.get("/list")
        self.assertEqual(resp.status_code, 200)
        items = resp.get_json()
        self.assertTrue(all(item.get("site") != "site" for item in items))
        self.client.post("/account/logout")

    def test_account_create_valid_and_duplicate_and_missing_fields(self):
        # missing fields should return 400
        r = self.client.post("/account/create", json={"username": "unittest-ca-1"})
        self.assertEqual(r.status_code, 400)
        r = self.client.post("/account/create", json={"master_password": "pw"})
        self.assertEqual(r.status_code, 400)

        # create success should return 201
        random_username = ''.join(random.choices(string.digits, k=10))
        r = self.client.post("/account/create", json={"username": random_username, "master_password": "pw"})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.get_json().get("status"), "account created")

        # duplicate should return 409
        r = self.client.post("/account/create", json={"username": random_username, "master_password": "pw"})
        self.assertEqual(r.status_code, 409)

    def test_account_login_variants(self):
        # missing fields should return 401
        r = self.client.post("/account/login", json={"username": "u"})
        self.assertEqual(r.status_code, 401)
        r = self.client.post("/account/login", json={"master_password": "p"})
        self.assertEqual(r.status_code, 401)

        # unknown user should return 401
        r = self.client.post("/account/login", json={"username": "unittest-nope", "master_password": "pw"})
        self.assertEqual(r.status_code, 401)

        # create account
        self.client.post("/account/create", json={"username": "unittest-login", "master_password": "secret"})

        # wrong password should return 401
        r = self.client.post("/account/login", json={"username": "unittest-login", "master_password": "bad"})
        self.assertEqual(r.status_code, 401)

        # lock first, then correct login should unlock and return 200
        self.client.post("/lock")
        r = self.client.post("/account/login", json={"username": "unittest-login", "master_password": "secret"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json().get("status"), "logged in")
        status = self.client.get("/status").get_json()
        self.assertFalse(status.get("vault_locked", True))
        
    # tests which are redundant in practice but get to 100% coverage #############################################
    def test_status_and_lock_unlock_cycle(self):
        # initial status after login in setUpClass should be unlocked
        res = self.client.get("/status").get_json()
        self.assertIn("vault_locked", res)

        # lock, then status
        self.client.post("/lock")
        self.assertTrue(self.client.get("/status").get_json()["vault_locked"])

        # unlock
        self.client.post("/unlock")
        self.assertFalse(self.client.get("/status").get_json()["vault_locked"])

    def test_add_rejects_when_locked(self):
        self.client.post("/lock")
        r = self.client.post("/add", json={"site":"s","username":"u","password":"p"})
        self.assertEqual(r.status_code, 423)  # locked
        # restore
        self.client.post("/unlock")
        self.client.post("/account/login", json={"username":"unittest-user","master_password":"unittest-pass"})

    def test_add_rejects_when_not_logged_in(self):
        # ensure unlocked + not logged in (lock clears vmk, unlock leaves it cleared)
        self.client.post("/lock")
        self.client.post("/unlock")
        r = self.client.post("/add", json={"site":"s","username":"u","password":"p"})
        self.assertEqual(r.status_code, 401)  # not logged in
        # re-login for subsequent tests
        self.client.post("/account/login", json={"username":"unittest-user","master_password":"unittest-pass"})

    def test_get_not_found_and_errors(self):
        # not found
        r = self.client.get("/get/999999")
        self.assertEqual(r.status_code, 404)

        # locked
        self.client.post("/lock")
        self.assertEqual(self.client.get("/get/1").status_code, 423)
        self.client.post("/unlock")

        # not logged in
        self.client.post("/account/logout")
        # logout locks the vault; unlock to test 401 path
        self.client.post("/unlock")
        self.assertEqual(self.client.get("/get/1").status_code, 401)
        self.client.post("/account/login", json={"username":"unittest-user","master_password":"unittest-pass"})

    def test_list_errors_when_locked_and_not_logged_in(self):
        self.client.post("/lock")
        self.assertEqual(self.client.get("/list").status_code, 423)
        self.client.post("/unlock")

        self.client.post("/account/logout")
        # logout locks the vault; unlock to test 401 path
        self.client.post("/unlock")
        self.assertEqual(self.client.get("/list").status_code, 401)
        self.client.post("/account/login", json={"username":"unittest-user","master_password":"unittest-pass"})

    def test_delete_errors_and_not_found(self):
        # not found
        self.assertEqual(self.client.delete("/delete/999999").status_code, 404)

        # locked
        self.client.post("/lock")
        self.assertEqual(self.client.delete("/delete/1").status_code, 423)
        self.client.post("/unlock")

        # not logged in
        self.client.post("/account/logout")
        self.client.post("/unlock")
        self.assertEqual(self.client.delete("/delete/1").status_code, 401)
        self.client.post("/account/login", json={"username":"unittest-user","master_password":"unittest-pass"})

    def test_update_errors_and_success(self):
        # ensure logged in for creation
        self.client.post("/account/login", json={"username":"unittest-user","master_password":"unittest-pass"})
        # create a row first
        add = self.client.post("/add", json={"site":"updsite","username":"u","password":"p"})
        self.assertEqual(add.status_code, 201)
        cid = add.get_json().get("id")
        self.assertIsNotNone(cid)

        # missing id
        self.assertEqual(self.client.put("/update", json={"password":"np"}).status_code, 400)

        # locked
        self.client.post("/lock")
        self.assertEqual(self.client.put("/update", json={"id":cid,"password":"np"}).status_code, 423)
        self.client.post("/unlock")

        # not logged in
        self.client.post("/account/logout")
        # logout locks vault; unlock to test 401
        self.client.post("/unlock")
        self.assertEqual(self.client.put("/update", json={"id":cid,"password":"np"}).status_code, 401)

        # success (relogin)
        self.client.post("/account/login", json={"username":"unittest-user","master_password":"unittest-pass"})
        r = self.client.put("/update", json={"id":cid,"password":"np"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json().get("status"), "updated")

    def test_generate_password_default(self):
        r = self.client.get("/get/generated-password")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertIn("password", data)
        pw = data["password"]
        self.assertIsInstance(pw, str)
        self.assertEqual(len(pw), 12)
        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()")
        self.assertTrue(all(ch in allowed for ch in pw))

    def test_ensure_credentials_id_column_migration(self):
        # Save originals
        old_conn = pm.conn
        old_c = pm.c
        try:
            # Create temp DB without id column
            tmp_fd, tmp_path = tempfile.mkstemp(prefix="vault_test_", suffix=".db")
            os.close(tmp_fd)
            new_conn = sqlite3.connect(tmp_path, check_same_thread=False)
            new_c = new_conn.cursor()
            new_c.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                site TEXT,
                username TEXT,
                password BLOB
            )
            """)
            new_conn.commit()

            # Swap globals
            pm.conn = new_conn
            pm.c = new_c

            # Run migration
            pm.ensure_credentials_id_column()

            # Assert id column exists
            new_c.execute("PRAGMA table_info(credentials)")
            cols = [row[1] for row in new_c.fetchall()]
            self.assertIn("id", cols)
        finally:
            # Cleanup and restore
            new_conn.close()
            os.remove(tmp_path)
            pm.conn = old_conn
            pm.c = old_c