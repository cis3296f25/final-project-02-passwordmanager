import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from passwordmanager.core.secure_cleanup import zero_bytearray_in_memory, cleanup_secrets


class TestSecureCleanup(unittest.TestCase):
    def test_zero_bytearray_in_memory_with_bytearray(self):
        data = bytearray(b"test_secret_data")
        original_len = len(data)
        zero_bytearray_in_memory(data)
        self.assertEqual(len(data), original_len)
        self.assertEqual(data, bytearray(b'\x00' * original_len))

    def test_zero_bytearray_in_memory_with_none(self):
        zero_bytearray_in_memory(None)

    def test_zero_bytearray_in_memory_with_bytes(self):
        data = b"test_secret_data"
        zero_bytearray_in_memory(data)
        self.assertEqual(data, b"test_secret_data")
    
    def test_zero_bytearray_in_memory_with_string(self):
        # test to cover branch: data is not None but not a bytearray
        data = "not a bytearray"
        zero_bytearray_in_memory(data)
        self.assertEqual(data, "not a bytearray")

    def test_zero_bytearray_in_memory_with_empty(self):
        data = bytearray()
        zero_bytearray_in_memory(data)
        self.assertEqual(len(data), 0)

    def test_cleanup_secrets_no_secrets(self):
        cleanup_secrets()

    def test_cleanup_secrets_with_vmk_bytes(self):
        from passwordmanager.api.routes import current_vmk
        original_vmk = current_vmk
        
        try:
            from passwordmanager.api.routes import current_vmk
            import passwordmanager.api.routes as routes_module
            routes_module.current_vmk = b"test_vmk_key_data"
            cleanup_secrets()
        finally:
            routes_module.current_vmk = original_vmk

    def test_cleanup_secrets_with_vmk_bytearray(self):
        from passwordmanager.api.routes import current_vmk
        original_vmk = current_vmk
        
        try:
            import passwordmanager.api.routes as routes_module
            routes_module.current_vmk = bytearray(b"test_vmk_key_data")
            cleanup_secrets()
        finally:
            routes_module.current_vmk = original_vmk
    
    def test_cleanup_secrets_with_vmk_other_type(self):
        # test to cover branch: current_vmk is not None but not bytearray or bytes
        import passwordmanager.api.routes as routes_module
        original_vmk = routes_module.current_vmk
        
        try:
            routes_module.current_vmk = "not bytes or bytearray"
            cleanup_secrets()
        finally:
            routes_module.current_vmk = original_vmk

    def test_cleanup_secrets_with_cipher(self):
        from cryptography.fernet import Fernet
        from passwordmanager.api.routes import current_vmk_cipher
        original_cipher = current_vmk_cipher
        
        try:
            import passwordmanager.api.routes as routes_module
            key = Fernet.generate_key()
            routes_module.current_vmk_cipher = Fernet(key)
            cleanup_secrets()
        finally:
            routes_module.current_vmk_cipher = original_cipher
    
    def test_cleanup_secrets_with_cipher_no_signing_key(self):
        # test to cover branch: hasattr returns False or _signing_key is None
        from cryptography.fernet import Fernet
        import passwordmanager.api.routes as routes_module
        original_cipher = routes_module.current_vmk_cipher
        
        try:
            key = Fernet.generate_key()
            cipher = Fernet(key)
            if hasattr(cipher, '_signing_key'):
                cipher._signing_key = None
            routes_module.current_vmk_cipher = cipher
            cleanup_secrets()
        finally:
            routes_module.current_vmk_cipher = original_cipher
    
    def test_cleanup_secrets_with_cipher_no_encryption_key(self):
        # test to cover branch: hasattr returns False or _encryption_key is None
        from cryptography.fernet import Fernet
        import passwordmanager.api.routes as routes_module
        original_cipher = routes_module.current_vmk_cipher
        
        try:
            key = Fernet.generate_key()
            cipher = Fernet(key)
            if hasattr(cipher, '_encryption_key'):
                cipher._encryption_key = None
            routes_module.current_vmk_cipher = cipher
            cleanup_secrets()
        finally:
            routes_module.current_vmk_cipher = original_cipher
    
    def test_cleanup_secrets_with_cipher_no_keys(self):
        # test to cover branches: both keys are None
        from cryptography.fernet import Fernet
        import passwordmanager.api.routes as routes_module
        original_cipher = routes_module.current_vmk_cipher
        
        try:
            key = Fernet.generate_key()
            cipher = Fernet(key)
            if hasattr(cipher, '_signing_key'):
                cipher._signing_key = None
            if hasattr(cipher, '_encryption_key'):
                cipher._encryption_key = None
            routes_module.current_vmk_cipher = cipher
            cleanup_secrets()
        finally:
            routes_module.current_vmk_cipher = original_cipher
    
    def test_cleanup_secrets_with_cipher_no_attrs(self):
        # test to cover branches: hasattr returns False for both attributes
        import passwordmanager.api.routes as routes_module
        original_cipher = routes_module.current_vmk_cipher
        
        class MockCipher:
            pass
        
        try:
            routes_module.current_vmk_cipher = MockCipher()
            cleanup_secrets()
        finally:
            routes_module.current_vmk_cipher = original_cipher
