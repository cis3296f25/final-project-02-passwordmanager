import unittest
from passwordManager import app, c, conn

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
        pwd  = "TestPassword"

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
