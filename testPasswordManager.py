import unittest
from passwordManager import app, c, conn, generate_password_str

class TestVaultAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()

    def tearDown(self):
        c.execute("DELETE FROM credentials WHERE site LIKE 'unittest-%'")
        conn.commit()

    def test_add_get_delete_roundtrip(self):
        site = "unittest-example.com"
        user = "tester"
        pwd  = generate_password_str(12)

        r = self.client.post("/add", json={"site": site, "username": user, "password": pwd})
        self.assertEqual(r.status_code, 200)

        r = self.client.get(f"/get/{site}")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertEqual(data["username"], user)
        self.assertEqual(data["password"], pwd)

        # delete returns the deleted record in current API
        r = self.client.delete(f"/delete/{site}")
        self.assertEqual(r.status_code, 200)
        j = r.get_json()
        self.assertTrue(j.get("site") == site or j.get("status") == "deleted")

        r = self.client.get(f"/get/{site}")
        self.assertEqual(r.get_json().get("error"), "not found")

    def test_password_generator_quality(self):
        r = self.client.get("/get/generated-password?length=20")
        self.assertEqual(r.status_code, 200)
        p = r.get_json()["password"]
        self.assertGreaterEqual(len(p), 20)
        self.assertTrue(any(c.islower() for c in p))
        self.assertTrue(any(c.isupper() for c in p))
        self.assertTrue(any(c.isdigit() for c in p))
        self.assertTrue(any(c in "!@#$%^&*()" for c in p))

if __name__ == "__main__":
    unittest.main(verbosity=2)
