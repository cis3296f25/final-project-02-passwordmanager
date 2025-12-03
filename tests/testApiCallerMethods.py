import unittest
import threading
import time
import random
import string
from unittest.mock import patch
from passwordmanager.api.routes import app
from passwordmanager.api.apiCallerMethods import *
import passwordmanager.api.apiCallerMethods as acm
from passwordmanager.core.passwordManager import c, conn

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
        cls.password = "TestPass123!" + "".join(random.choices(string.ascii_letters + string.digits, k=4))
        acm.account_create(cls.username, cls.password)
        acm.account_login(cls.username, cls.password)

    def test_list_returns_json(self):
        data = acm.get_all_credentials()
        self.assertIsInstance(data, list)

    def test_get_all_credentials(self):
        data = acm.get_all_credentials()
        self.assertIsInstance(data, list)
        # Verify created_at is formatted correctly for all credentials (coverage for line 219)
        for cred in data:
            if cred.get("created_at"):
                self.assertIsInstance(cred.get("created_at"), str)
                # Should be in MM-DD-YYYY format
                parts = cred.get("created_at").split("-")
                if len(parts) == 3:
                    self.assertEqual(len(parts[0]), 2)  # month
                    self.assertEqual(len(parts[1]), 2)  # day
                    self.assertEqual(len(parts[2]), 4)  # year

    def test_get_credential(self):
        # create isolated credential
        site = "acm-get-" + "".join(random.choices(string.digits, k=6))
        acm.add_credential(site, "apiuser", "ApiPass123!")
        creds = acm.get_all_credentials()
        match = next((i for i in creds if i.get("site") == site), None)
        self.assertIsNotNone(match, "credential not found after creation")
        cred_id = match.get("id")
        data = acm.get_credential(cred_id)
        self.assertIsInstance(data, dict)
        self.assertEqual(data.get("id"), cred_id)
        # Verify created_at is formatted correctly (coverage for line 99)
        if data.get("created_at"):
            self.assertIsInstance(data.get("created_at"), str)
            # Should be in MM-DD-YYYY format
            parts = data.get("created_at").split("-")
            self.assertEqual(len(parts), 3)
            self.assertEqual(len(parts[0]), 2)  # month
            self.assertEqual(len(parts[1]), 2)  # day
            self.assertEqual(len(parts[2]), 4)  # year
        # cleanup
        acm.delete_credential(cred_id)

    def test_get_new_generated_password(self):
        data = acm.get_new_generated_password()
        self.assertIsInstance(data, dict)
        pw = data.get("password")
        self.assertIsInstance(pw, str)
        self.assertEqual(len(pw), 16)

    def test_update_credential(self):
        # create a credential
        site = "acm-upd-" + "".join(random.choices(string.digits, k=6))
        username = "apiuser"
        acm.add_credential(site, username, "OldPass123!")
        creds = acm.get_all_credentials()
        match = next((i for i in creds if i.get("site") == site), None)
        self.assertIsNotNone(match, "credential not found after creation")
        cred_id = match.get("id")
        # exercise PUT update and response.json()
        result = acm.update_credential(cred_id, site, username, "NewPass123!")
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "updated")
        self.assertEqual(result.get("id"), cred_id)
        # verify update took effect
        fetched = acm.get_credential(cred_id)
        self.assertEqual(fetched.get("password"), "NewPass123!")
        # cleanup
        acm.delete_credential(cred_id)

    def test_delete_credential(self):
        # create then delete isolated credential
        site = "acm-del-" + "".join(random.choices(string.digits, k=6))
        acm.add_credential(site, "apiuser", "ApiPass123!")
        creds = acm.get_all_credentials()
        match = next((i for i in creds if i.get("site") == site), None)
        self.assertIsNotNone(match, "credential not found after creation")
        cred_id = match.get("id")
        data = acm.delete_credential(cred_id)
        self.assertIsInstance(data, dict)
        self.assertEqual(data.get("id"), cred_id)

    def test_add_credential(self):
        # dedicated test for add_credential function
        site = "acm-add-" + "".join(random.choices(string.digits, k=6))
        username = "testuser"
        password = "TestPass123!"
        result = acm.add_credential(site, username, password)
        self.assertIsInstance(result, dict)
        self.assertIn("id", result)
        self.assertEqual(result.get("status"), "added")
        # cleanup
        cred_id = result.get("id")
        acm.delete_credential(cred_id)

    def test_account_create_and_login(self):
        # dedicated test for account functions
        test_username = "test_account_" + "".join(random.choices(string.digits, k=6))
        test_password = "TestPass123!" + "".join(random.choices(string.ascii_letters + string.digits, k=4))
        create_result = acm.account_create(test_username, test_password)
        self.assertIsInstance(create_result, dict)
        self.assertEqual(create_result.get("status"), "account created")
        
        login_result = acm.account_login(test_username, test_password)
        self.assertIsInstance(login_result, dict)
        self.assertEqual(login_result.get("status"), "logged in")

    def test_set_master_password(self):
        new_password = "NewMasterPass123!" + "".join(random.choices(string.ascii_letters + string.digits, k=4))
        result = acm.set_master_password(new_password)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "password updated")

    def test_check_duplicate_credential(self):
        site = "acm-dup-" + "".join(random.choices(string.digits, k=6))
        username = "dupuser"
        result = acm.check_duplicate_credential(site, username)
        self.assertIsInstance(result, dict)
        self.assertIn("exists", result)
        self.assertFalse(result.get("exists"))
        
        acm.add_credential(site, username, "TestPass123!")
        result = acm.check_duplicate_credential(site, username)
        self.assertIsInstance(result, dict)
        self.assertIn("exists", result)
        self.assertTrue(result.get("exists"))
        
        creds = acm.get_all_credentials()
        match = next((i for i in creds if i.get("site") == site), None)
        if match:
            acm.delete_credential(match.get("id"))

    def test_account_logout(self):
        result = acm.account_logout()
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "vault locked")
        
        status = acm.get_status()
        self.assertTrue(status.get("vault_locked"))
        
        acm.account_login(self.username, self.password)
    
    def test_export_credentials_json(self):
        # Test JSON export (default)
        result = acm.export_credentials("json")
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)
        self.assertIn("version", result)
        
        # Test default (no parameter)
        result_default = acm.export_credentials()
        self.assertIsInstance(result_default, dict)
        self.assertIn("items", result_default)
        self.assertIn("version", result_default)
        
        # Test case insensitive
        result_upper = acm.export_credentials("JSON")
        self.assertIsInstance(result_upper, dict)
        self.assertIn("items", result_upper)
    
    def test_export_credentials_csv(self):
        # Test CSV export
        result = acm.export_credentials("csv")
        self.assertIsInstance(result, str)
        self.assertIn("site", result.lower())
        self.assertIn("username", result.lower())
        self.assertIn("password", result.lower())
        
        # Test case insensitive
        result_upper = acm.export_credentials("CSV")
        self.assertIsInstance(result_upper, str)
    
    def test_export_credentials_none_format(self):
        # Test None format defaults to json
        result = acm.export_credentials(None)
        self.assertIsInstance(result, dict)
    
    def test_import_credentials_csv(self):
        # Create test CSV data
        csv_data = "site,username,password\ntest-site-import,testuser,TestPass123!"
        
        # Test import without allowing duplicates
        result = acm.import_credentials_csv(csv_data, allow_duplicates=False)
        self.assertIsInstance(result, dict)
        self.assertIn("inserted", result)
        self.assertIn("skipped", result)
        
        # Cleanup
        creds = acm.get_all_credentials()
        match = next((i for i in creds if i.get("site") == "test-site-import"), None)
        if match:
            acm.delete_credential(match.get("id"))
    
    def test_import_credentials_csv_allow_duplicates(self):
        # First add a credential
        site = "test-dup-import"
        username = "dupuser"
        acm.add_credential(site, username, "OriginalPass123!")
        
        # Create CSV with duplicate
        csv_data = f"site,username,password\n{site},{username},NewPass123!"
        
        # Test import with allow_duplicates=False (should skip)
        result = acm.import_credentials_csv(csv_data, allow_duplicates=False)
        self.assertIsInstance(result, dict)
        self.assertGreaterEqual(result.get("skipped", 0), 1)
        
        # Test import with allow_duplicates=True (should insert)
        result_allow = acm.import_credentials_csv(csv_data, allow_duplicates=True)
        self.assertIsInstance(result_allow, dict)
        self.assertGreaterEqual(result_allow.get("inserted", 0), 1)
        
        # Cleanup - delete all instances
        creds = acm.get_all_credentials()
        for cred in creds:
            if cred.get("site") == site and cred.get("username") == username:
                acm.delete_credential(cred.get("id"))
    
    def test_account_lockout_status(self):
        result = acm.account_lockout_status()
        self.assertIsInstance(result, dict)
        self.assertIn("locked", result)
        self.assertIn("lockout_seconds", result)
    
    def test_get_credential_created_at_datetime_formatting(self):
        # Test coverage for line 99: created_at as datetime.datetime
        site = "acm-datetime-" + "".join(random.choices(string.digits, k=6))
        acm.add_credential(site, "user", "Pass123!")
        creds = acm.get_all_credentials()
        match = next((i for i in creds if i.get("site") == site), None)
        self.assertIsNotNone(match)
        cred_id = match.get("id")
        
        data = acm.get_credential(cred_id)
        # Verify created_at exists and is formatted (covers datetime path if datetime object returned)
        self.assertIn("created_at", data)
        if data.get("created_at"):
            self.assertIsInstance(data.get("created_at"), str)
        
        acm.delete_credential(cred_id)
    
    def test_list_credentials_created_at_datetime_formatting(self):
        # Test coverage for line 219: created_at as datetime.datetime in list
        site = "acm-list-dt-" + "".join(random.choices(string.digits, k=6))
        acm.add_credential(site, "user", "Pass123!")
        
        creds = acm.get_all_credentials()
        match = next((i for i in creds if i.get("site") == site), None)
        self.assertIsNotNone(match)
        
        # Verify created_at exists and is formatted (covers datetime path if datetime object returned)
        self.assertIn("created_at", match)
        if match.get("created_at"):
            self.assertIsInstance(match.get("created_at"), str)
        
        acm.delete_credential(match.get("id"))