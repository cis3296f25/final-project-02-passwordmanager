import base64
from typing import Optional, Dict, Any
from argon2.low_level import hash_secret_raw, Type as Argon2Type

# a lot of these parameters are just the defaults for Argon2id
# they could also be almost anything and this would still work
def default_kdf_params() -> Dict[str, Any]:
    return {
        "time_cost": 3,
        "memory_cost": 65536,  # 64 MiB
        "parallelism": 2,
        "hash_len": 32,
        "version": 19,
        "type": "argon2id",
    }


def derive_wrap_key(master_password: str, salt: bytes, params: Optional[Dict[str, Any]] = None) -> bytes:
    cfg = {**default_kdf_params(), **(params or {})}
    dk = hash_secret_raw(
        secret=master_password.encode("utf-8"),
        salt=salt,
        time_cost=cfg["time_cost"],
        memory_cost=cfg["memory_cost"],
        parallelism=cfg["parallelism"],
        hash_len=cfg["hash_len"],
        type=Argon2Type.ID,
        version=cfg["version"],
    )
    # Fernet expects a urlsafe base64-encoded 32-byte key
    return base64.urlsafe_b64encode(dk)


