import hashlib
import hmac
import secrets


_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 310_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _ITERATIONS,
    )
    return f"{_ALGORITHM}${_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_password: str) -> tuple[bool, bool]:
    if not stored_password.startswith(_ALGORITHM + "$"):
        return hmac.compare_digest(password, stored_password), True

    try:
        algorithm, iterations, salt_hex, digest_hex = stored_password.split("$")
        if algorithm != _ALGORITHM:
            return False, False
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
    except (ValueError, TypeError):
        return False, False

    return hmac.compare_digest(actual, expected), int(iterations) < _ITERATIONS
