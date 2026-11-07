import base64
import binascii
import hashlib
import hmac
import os
import secrets
import time


SESSION_COOKIE = "wuri_session"
SESSION_TTL_SECONDS = 3600


def hash_password(password: str) -> str:
    if len(password) < 12:
        raise ValueError("Password must contain at least 12 characters.")
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt$16384$8$1${_encode(salt)}${_encode(digest)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, n, r, p, salt, expected = encoded.split("$")
        if algorithm != "scrypt":
            return False
        actual = hashlib.scrypt(
            password.encode(),
            salt=_decode(salt),
            n=int(n),
            r=int(r),
            p=int(p),
        )
        return hmac.compare_digest(actual, _decode(expected))
    except (ValueError, TypeError, OverflowError, binascii.Error):
        return False


def create_session_token(user_id: str, secret: str) -> str:
    expires = str(int(time.time()) + SESSION_TTL_SECONDS)
    payload = f"{user_id}.{expires}".encode()
    signature = hmac.new(secret.encode(), payload, hashlib.sha256).digest()
    return f"{_encode(payload)}.{_encode(signature)}"


def read_session_token(token: str | None, secret: str) -> str | None:
    if not token:
        return None
    try:
        payload_text, signature_text = token.split(".")
        payload = _decode(payload_text)
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _decode(signature_text)):
            return None
        user_id, expires = payload.decode().split(".")
        if int(expires) < int(time.time()):
            return None
        return user_id
    except (ValueError, TypeError, UnicodeDecodeError, binascii.Error):
        return None


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
