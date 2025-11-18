from cryptography.fernet import Fernet

# in general, this is just a wrapper to call Fernet functions
def generate_vmk() -> bytes:
    return Fernet.generate_key()


def wrap_vmk(wrap_key: bytes, vmk_key_b64: bytes) -> bytes:
    return Fernet(wrap_key).encrypt(vmk_key_b64)


def unwrap_vmk(wrap_key: bytes, wrapped_vmk_token: bytes) -> bytes:
    return Fernet(wrap_key).decrypt(wrapped_vmk_token)


