import unittest
import random
import string
import sqlite3
import tempfile
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import patch
from passwordmanager.api.routes import app
from passwordmanager.core.passwordManager import c, conn
import passwordmanager.core.passwordManager as pm

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
        c.execute("DELETE FROM login_lockout WHERE id = 1")
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

    def test_account_password_change_flow(self):
        # create a new user for this test. we don't have a method to delete accounts yet and
        # there are no repeat usernames allowed, so for now username is a random string of length 50
        username = ''.join(random.choices(string.ascii_letters + string.digits, k=50))
        old_pw = "old_master_pw"
        new_pw = "new_master_pw"


        self.client.post("/account/create",
                         json={"username": username, "master_password": old_pw})

        # login to dummy account with old_master_pw
        r = self.client.post("/account/login",
                             json={"username": username, "master_password": old_pw})
        self.assertEqual(r.status_code, 200)

        # get current wrapped vmk before change for comparison
        c.execute("SELECT wrapped_vmk FROM user_metadata WHERE username = ?", (username,))
        row_before = c.fetchone()
        self.assertIsNotNone(row_before)
        wrapped_before = row_before[0]

        # trying to change the master password without including a password parameter shuld return 400
        bad = self.client.put("/account/password", json={})
        self.assertEqual(bad.status_code, 400)

        # successful password change should return 200
        r = self.client.put("/account/password",
                            json={"new_password": new_pw})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json().get("status"), "password updated")

        # get the wrapped vmk again, it should be different now
        c.execute("SELECT wrapped_vmk FROM user_metadata WHERE username = ?", (username,))
        row_after = c.fetchone()
        self.assertIsNotNone(row_after)
        wrapped_after = row_after[0]

        self.assertNotEqual(wrapped_before, wrapped_after,
                            "wrapped VMK must change after password rotation")

        # login to dummy account with old password should fail
        self.client.post("/account/logout")
        r = self.client.post("/account/login",
                             json={"username": username, "master_password": old_pw})
        self.assertEqual(r.status_code, 401)

        # login to dummy account with new password should return succeed
        r = self.client.post("/account/login",
                             json={"username": username, "master_password": new_pw})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json().get("status"), "logged in")


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
        c.execute("DELETE FROM login_lockout WHERE id = 1")
        conn.commit()

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
        # Generate strong passwords for this test
        initial_password = "Pass123!" + "".join(random.choices(string.ascii_letters + string.digits, k=4))
        update_password = "NewPass123!" + "".join(random.choices(string.ascii_letters + string.digits, k=4))
        
        # ensure logged in for creation
        self.client.post("/account/login", json={"username":"unittest-user","master_password":"unittest-pass"})
        # create a row first
        add = self.client.post("/add", json={"site":"updsite","username":"u","password":initial_password})
        self.assertEqual(add.status_code, 201)
        cid = add.get_json().get("id")
        self.assertIsNotNone(cid)

        # missing id
        self.assertEqual(self.client.put("/update", json={"site":"updsite","username":"u","password":update_password}).status_code, 400)

        # locked
        self.client.post("/lock")
        self.assertEqual(self.client.put("/update", json={"id":cid,"site":"updsite","username":"u","password":update_password}).status_code, 423)
        self.client.post("/unlock")

        # not logged in
        self.client.post("/account/logout")
        # logout locks vault; unlock to test 401
        self.client.post("/unlock")
        self.assertEqual(self.client.put("/update", json={"id":cid,"site":"updsite","username":"u","password":update_password}).status_code, 401)

        # success (relogin)
        self.client.post("/account/login", json={"username":"unittest-user","master_password":"unittest-pass"})
        r = self.client.put("/update", json={"id":cid,"site":"updsite","username":"u","password":update_password})
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
            
    def test_db_path(self):
        self.assertIsNotNone(pm.db_path)
    
    def test_get_base_path_frozen(self):
        with patch.object(pm.sys, 'frozen', True, create=True):
            with patch.object(pm.sys, 'executable', '/fake/path/to/executable'):
                expected_path = os.path.dirname('/fake/path/to/executable')
                result = pm.get_base_path()
                self.assertEqual(result, expected_path)

    def test_change_master_password_when_locked(self):
        self.client.post("/lock")
        r = self.client.put("/account/password", json={"new_password": "newpass"})
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.get_json().get("error"), "not logged in")
        self.client.post("/unlock")
        self.client.post("/account/login", json={"username":"unittest-user","master_password":"unittest-pass"})

    def test_change_master_password_when_not_logged_in(self):
        self.client.post("/account/logout")
        self.client.post("/unlock")
        r = self.client.put("/account/password", json={"new_password": "newpass"})
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.get_json().get("error"), "not logged in")
        self.client.post("/account/login", json={"username":"unittest-user","master_password":"unittest-pass"})

    def test_change_master_password_user_not_found(self):
        test_username = "unittest-notfound-" + "".join(random.choices(string.digits, k=6))
        test_password = "TestPass123!"
        self.client.post("/account/create", json={"username": test_username, "master_password": test_password})
        self.client.post("/account/login", json={"username": test_username, "master_password": test_password})
        c.execute("DELETE FROM user_metadata WHERE username = ?", (test_username,))
        conn.commit()
        r = self.client.put("/account/password", json={"new_password": "newpass"})
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.get_json().get("error"), "user not found")
        self.client.post("/account/login", json={"username":"unittest-user","master_password":"unittest-pass"})

    def test_check_duplicate_when_locked(self):
        self.client.post("/lock")
        r = self.client.post("/check-duplicate", json={"site": "example.com", "username": "user"})
        self.assertEqual(r.status_code, 423)
        self.assertEqual(r.get_json().get("error"), "Vault is locked")
        self.client.post("/unlock")
        self.client.post("/account/login", json={"username":"unittest-user","master_password":"unittest-pass"})

    def test_check_duplicate_not_exists(self):
        site = "unittest-dup-check-" + "".join(random.choices(string.digits, k=6))
        username = "uniqueuser"
        r = self.client.post("/check-duplicate", json={"site": site, "username": username})
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertIn("exists", data)
        self.assertFalse(data.get("exists"))

    def test_check_duplicate_exists(self):
        site = "unittest-dup-exists-" + "".join(random.choices(string.digits, k=6))
        username = "dupuser"
        self.client.post("/add", json={"site": site, "username": username, "password": "TestPass123!"})
        r = self.client.post("/check-duplicate", json={"site": site, "username": username})
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertIn("exists", data)
        self.assertTrue(data.get("exists"))
        creds = self.client.get("/list").get_json()
        match = next((i for i in creds if i.get("site") == site and i.get("username") == username), None)
        if match:
            self.client.delete(f"/delete/{match.get('id')}")
