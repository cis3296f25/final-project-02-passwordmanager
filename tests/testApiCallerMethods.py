import unittest
import threading
import time
import random
import string
from passwordManager import app
import apiCallerMethods as acm

class TestApiCallerMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # start server in background
        app.config["TESTING"] = True
        cls.server_thread = threading.Thread(
            target=app.run, kwargs={"port": 5000, "use_reloader": False}, daemon=True
        )
        cls.server_thread.start()
        # wait for server readiness
        for _ in range(50):
            status = acm.get_status()
            if isinstance(status, dict):
                break
            time.sleep(0.1)
        # ensure an account and login
        cls.username = "acm_user_" + "".join(random.choices(string.digits, k=6))
        cls.password = "acm_pw_" + "".join(random.choices(string.ascii_letters, k=6))
        acm.account_create(cls.username, cls.password)
        acm.account_login(cls.username, cls.password)

    def test_list_returns_json(self):
        data = acm.get_all_credentials()
        self.assertIsInstance(data, list)

    def test_get_all_credentials(self):
        data = acm.get_all_credentials()
        self.assertIsInstance(data, list)

    def test_get_credential(self):
        # create isolated credential
        site = "acm-get-" + "".join(random.choices(string.digits, k=6))
        acm.add_credential(site, "apiuser", "apipass")
        creds = acm.get_all_credentials()
        match = next((i for i in creds if i.get("site") == site), None)
        self.assertIsNotNone(match, "credential not found after creation")
        cred_id = match.get("id")
        data = acm.get_credential(cred_id)
        self.assertIsInstance(data, dict)
        self.assertEqual(data.get("id"), cred_id)
        # cleanup
        acm.delete_credential(cred_id)

    def test_get_new_generated_password(self):
        data = acm.get_new_generated_password()
        self.assertIsInstance(data, dict)
        pw = data.get("password")
        self.assertIsInstance(pw, str)
        self.assertEqual(len(pw), 12)

    def test_update_credential(self):
        # create a credential
        site = "acm-upd-" + "".join(random.choices(string.digits, k=6))
        username = "apiuser"
        acm.add_credential(site, username, "oldpass")
        creds = acm.get_all_credentials()
        match = next((i for i in creds if i.get("site") == site), None)
        self.assertIsNotNone(match, "credential not found after creation")
        cred_id = match.get("id")
        # exercise PUT update and response.json()
        result = acm.update_credential(cred_id, site, username, "newpass")
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "updated")
        self.assertEqual(result.get("id"), cred_id)
        # verify update took effect
        fetched = acm.get_credential(cred_id)
        self.assertEqual(fetched.get("password"), "newpass")
        # cleanup
        acm.delete_credential(cred_id)

    def test_delete_credential(self):
        # create then delete isolated credential
        site = "acm-del-" + "".join(random.choices(string.digits, k=6))
        acm.add_credential(site, "apiuser", "apipass")
        creds = acm.get_all_credentials()
        match = next((i for i in creds if i.get("site") == site), None)
        self.assertIsNotNone(match, "credential not found after creation")
        cred_id = match.get("id")
        data = acm.delete_credential(cred_id)
        self.assertIsInstance(data, dict)
        self.assertEqual(data.get("id"), cred_id)