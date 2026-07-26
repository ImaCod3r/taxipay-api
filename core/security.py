import base64
import hashlib
import hmac
import os

_ALGO = "sha256"
_ITERATIONS = 200_000
_SALT_BYTES = 16
_SCHEME = f"pbkdf2_{_ALGO}"

def _b64encode(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")

def _b64decode(text: str) -> bytes:
    return base64.b64decode(text.encode("ascii"))

def hash_pin(pin: str) -> str:
    """Gera o hash de um PIN para ser guardado no banco."""
    salt = os.urandom(_SALT_BYTES)
    derived = hashlib.pbkdf2_hmac(_ALGO, pin.encode("utf-8"), salt, _ITERATIONS)
    return f"{_SCHEME}${_ITERATIONS}${_b64encode(salt)}${_b64encode(derived)}"

def verify_pin(pin: str, hashed: str) -> bool:
    """Confere um PIN em texto puro contra o hash guardado."""
    try:
        scheme, iterations, salt_b64, hash_b64 = hashed.split("$")
        if scheme != _SCHEME:
            return False
        salt = _b64decode(salt_b64)
        expected = _b64decode(hash_b64)
        derived = hashlib.pbkdf2_hmac(_ALGO, pin.encode("utf-8"), salt, int(iterations))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(derived, expected)