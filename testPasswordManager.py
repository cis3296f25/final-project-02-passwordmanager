import unittest
import random
import string
from passwordManager import app, c, conn

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
