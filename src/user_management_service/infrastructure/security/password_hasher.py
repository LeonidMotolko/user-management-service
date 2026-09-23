import hashlib
import hmac
import os

from user_management_service.application.interfaces.password_hasher import (
    IPasswordHasher,
)


class PBKDF2PasswordHasher(IPasswordHasher):
    def __init__(
        self,
        algorithm: str = "sha256",
        iterations: int = 600000,
        salt_length: int = 16,
    ) -> None:
        self.algorithm = algorithm
        self.iterations = iterations
        self.salt_length = salt_length

    def hash(self, password: str) -> str:
        salt = os.urandom(self.salt_length)
        hash_bytes = hashlib.pbkdf2_hmac(
            self.algorithm,
            password.encode("utf-8"),
            salt,
            self.iterations,
        )
        return f"{salt.hex()}:{hash_bytes.hex()}"

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        try:
            salt_hex, hash_hex = hashed_password.split(":")
            salt = bytes.fromhex(salt_hex)
            expected_hash = bytes.fromhex(hash_hex)

            new_hash = hashlib.pbkdf2_hmac(
                self.algorithm,
                plain_password.encode("utf-8"),
                salt,
                self.iterations,
            )
            return hmac.compare_digest(new_hash, expected_hash)
        except (ValueError, TypeError):
            return False
