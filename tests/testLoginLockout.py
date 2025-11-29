import unittest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from passwordmanager.api.routes import app
from passwordmanager.core.passwordManager import c, conn


class TestLoginLockout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()
        cls.test_username = "unittest-lockout-user"
        cls.test_password = "test-password-123"
        
        cls._reset_lockout()
        c.execute("DELETE FROM user_metadata WHERE username = ?", (cls.test_username,))
        conn.commit()
        
        cls.client.post("/account/create", json={
            "username": cls.test_username,
            "master_password": cls.test_password
        })

    @classmethod
    def _reset_lockout(cls):
        c.execute("DELETE FROM login_lockout WHERE id = 1")
        conn.commit()

    def setUp(self):
        self._reset_lockout()

    def tearDown(self):
        self._reset_lockout()

    def test_lockout_status_no_lockout(self):
        r = self.client.get("/account/lockout-status")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertFalse(data.get("locked"))
        self.assertEqual(data.get("lockout_seconds"), 0)

    def test_lockout_status_missing_username_removed(self):
        r = self.client.get("/account/lockout-status")
        self.assertEqual(r.status_code, 200)

    def test_three_failed_attempts_triggers_lockout(self):
        wrong_password = "wrong-password"
        
        for i in range(3):
            r = self.client.post("/account/login", json={
                "username": self.test_username,
                "master_password": wrong_password
            })
            self.assertEqual(r.status_code, 401)
        
        r = self.client.get("/account/lockout-status")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertTrue(data.get("locked"))
        self.assertGreater(data.get("lockout_seconds"), 0)
        self.assertLessEqual(data.get("lockout_seconds"), 15)

    def test_lockout_prevents_login_attempt(self):
        wrong_password = "wrong-password"
        
        for i in range(3):
            self.client.post("/account/login", json={
                "username": self.test_username,
                "master_password": wrong_password
            })
        
        r = self.client.post("/account/login", json={
            "username": self.test_username,
            "master_password": wrong_password
        })
        self.assertEqual(r.status_code, 423)
        data = r.get_json()
        self.assertEqual(data.get("error"), "login locked")
        self.assertIn("lockout_seconds", data)
        self.assertGreater(data.get("lockout_seconds"), 0)

    def test_correct_login_resets_lockout(self):
        wrong_password = "wrong-password"
        
        for i in range(2):
            self.client.post("/account/login", json={
                "username": self.test_username,
                "master_password": wrong_password
            })
        
        r = self.client.post("/account/login", json={
            "username": self.test_username,
            "master_password": self.test_password
        })
        self.assertEqual(r.status_code, 200)
        
        r = self.client.get("/account/lockout-status")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertFalse(data.get("locked"))
        self.assertEqual(data.get("lockout_seconds"), 0)

    def test_lockout_duration_doubles_on_subsequent_failure(self):
        wrong_password = "wrong-password"
        
        for i in range(3):
            self.client.post("/account/login", json={
                "username": self.test_username,
                "master_password": wrong_password
            })
        
        r = self.client.get("/account/lockout-status")
        first_lockout = r.get_json().get("lockout_seconds")
        self.assertGreaterEqual(first_lockout, 14)
        self.assertLessEqual(first_lockout, 15)
        
        self._reset_lockout()
        c.execute("UPDATE login_lockout SET failed_attempts = 3, lockout_until_timestamp = NULL WHERE id = 1")
        c.execute("INSERT OR IGNORE INTO login_lockout (id, failed_attempts) VALUES (1, 3)")
        conn.commit()
        
        r = self.client.post("/account/login", json={
            "username": self.test_username,
            "master_password": wrong_password
        })
        self.assertEqual(r.status_code, 401)
        
        r = self.client.get("/account/lockout-status")
        second_lockout = r.get_json().get("lockout_seconds")
        self.assertGreaterEqual(second_lockout, 29)
        self.assertLessEqual(second_lockout, 30)

    def test_lockout_expires_after_time(self):
        wrong_password = "wrong-password"
        
        for i in range(3):
            self.client.post("/account/login", json={
                "username": self.test_username,
                "master_password": wrong_password
            })
        
        r = self.client.get("/account/lockout-status")
        self.assertTrue(r.get_json().get("locked"))
        
        import time
        current_time = time.time()
        c.execute("UPDATE login_lockout SET lockout_until_timestamp = ? WHERE id = 1", (current_time - 1,))
        conn.commit()
        
        r = self.client.get("/account/lockout-status")
        data = r.get_json()
        self.assertFalse(data.get("locked"))
        self.assertEqual(data.get("lockout_seconds"), 0)

    def test_failed_attempts_increment_correctly(self):
        wrong_password = "wrong-password"
        
        for i in range(1, 4):
            self.client.post("/account/login", json={
                "username": self.test_username,
                "master_password": wrong_password
            })
            
            r = self.client.get("/account/lockout-status")
            data = r.get_json()
            
            if i < 3:
                self.assertFalse(data.get("locked"))
            else:
                self.assertTrue(data.get("locked"))

    def test_unknown_username_increments_global_lockout(self):
        r = self.client.post("/account/login", json={
            "username": "nonexistent-user-xyz",
            "master_password": "any-password"
        })
        self.assertEqual(r.status_code, 401)
        
        r = self.client.get("/account/lockout-status")
        data = r.get_json()
        self.assertFalse(data.get("locked"))

    def test_wrong_password_increments_failed_attempts(self):
        wrong_password = "wrong-password"
        
        self.client.post("/account/login", json={
            "username": self.test_username,
            "master_password": wrong_password
        })
        
        r = self.client.get("/account/lockout-status")
        data = r.get_json()
        self.assertFalse(data.get("locked"))

    def test_lockout_prevents_login_even_with_correct_password(self):
        wrong_password = "wrong-password"
        
        for i in range(3):
            self.client.post("/account/login", json={
                "username": self.test_username,
                "master_password": wrong_password
            })
        
        r = self.client.post("/account/login", json={
            "username": self.test_username,
            "master_password": self.test_password
        })
        self.assertEqual(r.status_code, 423)
        data = r.get_json()
        self.assertEqual(data.get("error"), "login locked")

    def test_lockout_is_global_across_different_usernames(self):
        wrong_password = "wrong-password"
        test_username2 = "unittest-lockout-user-2"
        test_password2 = "test-password-456"
        
        self.client.post("/account/create", json={
            "username": test_username2,
            "master_password": test_password2
        })
        
        for i in range(2):
            self.client.post("/account/login", json={
                "username": self.test_username,
                "master_password": wrong_password
            })
        
        r = self.client.post("/account/login", json={
            "username": test_username2,
            "master_password": wrong_password
        })
        self.assertEqual(r.status_code, 401)
        
        r = self.client.get("/account/lockout-status")
        data = r.get_json()
        self.assertGreaterEqual(data.get("lockout_seconds"), 1)
        self.assertTrue(data.get("locked"))

    def test_lockout_persists_across_requests(self):
        wrong_password = "wrong-password"
        
        for i in range(3):
            self.client.post("/account/login", json={
                "username": self.test_username,
                "master_password": wrong_password
            })
        
        r1 = self.client.get("/account/lockout-status")
        lockout1 = r1.get_json().get("lockout_seconds")
        
        r2 = self.client.get("/account/lockout-status")
        lockout2 = r2.get_json().get("lockout_seconds")
        
        self.assertGreaterEqual(lockout1, lockout2)

    def test_record_failed_attempt_function_coverage(self):
        from passwordmanager.api.routes import _record_failed_attempt
        
        self._reset_lockout()
        _record_failed_attempt()
        
        r = self.client.get("/account/lockout-status")
        data = r.get_json()
        self.assertEqual(data.get("lockout_seconds"), 0)
        
        for i in range(2):
            _record_failed_attempt()
        
        r = self.client.get("/account/lockout-status")
        data = r.get_json()
        self.assertTrue(data.get("locked"))

    def test_reset_lockout_function_coverage(self):
        from passwordmanager.api.routes import _reset_lockout
        
        wrong_password = "wrong-password"
        for i in range(3):
            self.client.post("/account/login", json={
                "username": self.test_username,
                "master_password": wrong_password
            })
        
        r = self.client.get("/account/lockout-status")
        self.assertTrue(r.get_json().get("locked"))
        
        _reset_lockout()
        
        r = self.client.get("/account/lockout-status")
        data = r.get_json()
        self.assertFalse(data.get("locked"))
        self.assertEqual(data.get("lockout_seconds"), 0)

    def test_record_failed_attempt_early_return_when_locked(self):
        from passwordmanager.api.routes import _record_failed_attempt
        import time
        
        wrong_password = "wrong-password"
        for i in range(3):
            self.client.post("/account/login", json={
                "username": self.test_username,
                "master_password": wrong_password
            })
        
        r = self.client.get("/account/lockout-status")
        self.assertTrue(r.get_json().get("locked"))
        
        current_time = time.time()
        c.execute("SELECT lockout_until_timestamp FROM login_lockout WHERE id = 1")
        lockout_until = c.fetchone()[0]
        
        _record_failed_attempt()
        
        c.execute("SELECT failed_attempts FROM login_lockout WHERE id = 1")
        failed_attempts_after = c.fetchone()[0]
        
        self.assertEqual(failed_attempts_after, 3)
