# test_password_manager.py
import unittest
from passwordManager import app, c, conn, generate_password

class TestVaultAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()

    def tearDown(self):
        # clean any test data this test might have created
        c.execute("DELETE FROM credentials WHERE site LIKE 'unittest-%'")
        conn.commit()

    def test_add_get_delete_roundtrip(self):
        site = "unittest-example.com"
        user = "tester"
        pwd  = generate_password(12)

        # add
        r = self.client.post("/add", json={"site": site, "username": user, "password": pwd})
        self.assertEqual(r.status_code, 200)

        # get
        r = self.client.get(f"/get/{site}")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertEqual(data["username"], user)
        self.assertEqual(data["password"], pwd)

        # delete (your API currently returns the deleted record, not {"status":"deleted"})
        r = self.client.delete(f"/delete/{site}")
        self.assertEqual(r.status_code, 200)
        j = r.get_json()
        self.assertTrue(j.get("status") == "deleted" or j.get("site") == site)

        # verify gone
        r = self.client.get(f"/get/{site}")
        self.assertEqual(r.get_json().get("error"), "not found")

    def test_password_generator_quality(self):
        # smoke checks on length & variety
        p = generate_password(20)
        self.assertGreaterEqual(len(p), 20)
        # ensure we didn’t accidentally restrict chars to only lowercase, etc.
        self.assertTrue(any(c.islower() for c in p))
        self.assertTrue(any(c.isupper() for c in p))
        self.assertTrue(any(c.isdigit() for c in p))

if __name__ == "__main__":
    unittest.main(verbosity=2)
