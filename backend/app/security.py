import base64
import binascii
import hashlib
import hmac
import secrets
import time


SESSION_COOKIE = "wuri_session"
SESSION_TTL_SECONDS = 3600
MIN_SESSION_SECRET_BYTES = 32
PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 1024
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_MAX_MEMORY_BYTES = 64 * 1024 * 1024
SCRYPT_SALT_BYTES = 16
SCRYPT_DIGEST_BYTES = 64


def validate_session_secret(secret: str | None) -> str:
    if not isinstance(secret, str) or len(secret.encode("utf-8")) < MIN_SESSION_SECRET_BYTES:
        raise ValueError("WURI_SESSION_SECRET must contain at least 32 bytes.")
    if len(set(secret)) < 8:
        raise ValueError("WURI_SESSION_SECRET must not be a repeated or low-diversity value.")
    return secret


def hash_password(password: str) -> str:
    if not isinstance(password, str) or not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
        raise ValueError(
            f"Password must contain between {PASSWORD_MIN_LENGTH} and {PASSWORD_MAX_LENGTH} characters."
        )
    salt = secrets.token_bytes(SCRYPT_SALT_BYTES)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        maxmem=SCRYPT_MAX_MEMORY_BYTES,
        dklen=SCRYPT_DIGEST_BYTES,
    )
    return (
        f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}"
        f"${_encode(salt)}${_encode(digest)}"
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        if (
            not isinstance(password, str)
            or len(password) > PASSWORD_MAX_LENGTH
            or not isinstance(encoded, str)
            or len(encoded) > 512
        ):
            return False
        algorithm, n_text, r_text, p_text, salt_text, expected_text = encoded.split("$")
        # Parameters are fixed by this application. Never execute scrypt with
        # database-supplied work factors that could exhaust CPU or memory.
        if (
            algorithm != "scrypt"
            or (n_text, r_text, p_text)
            != (str(SCRYPT_N), str(SCRYPT_R), str(SCRYPT_P))
        ):
            return False
        salt = _decode(salt_text)
        expected = _decode(expected_text)
        if len(salt) != SCRYPT_SALT_BYTES or len(expected) != SCRYPT_DIGEST_BYTES:
            return False
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=SCRYPT_N,
            r=SCRYPT_R,
            p=SCRYPT_P,
            maxmem=SCRYPT_MAX_MEMORY_BYTES,
            dklen=SCRYPT_DIGEST_BYTES,
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, OverflowError, MemoryError, binascii.Error):
        return False


def create_session_token(user_id: str, secret: str) -> str:
    secret = validate_session_secret(secret)
    expires = str(int(time.time()) + SESSION_TTL_SECONDS)
    session_id = secrets.token_urlsafe(32)
    payload = f"{user_id}.{expires}.{session_id}".encode()
    signature = hmac.new(secret.encode(), payload, hashlib.sha256).digest()
    return f"{_encode(payload)}.{_encode(signature)}"


def read_session_claims(token: str | None, secret: str) -> dict[str, str | int] | None:
    try:
        secret = validate_session_secret(secret)
        if not token or len(token) > 2048:
            return None
        payload_text, signature_text = token.split(".")
        payload = _decode(payload_text)
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _decode(signature_text)):
            return None
        user_id, expires_text, session_id = payload.decode().split(".")
        expires_at = int(expires_text)
        if not user_id or not session_id or expires_at <= int(time.time()):
            return None
        return {"user_id": user_id, "expires_at": expires_at, "session_id": session_id}
    except (ValueError, TypeError, UnicodeDecodeError, binascii.Error):
        return None


def read_session_token(token: str | None, secret: str) -> str | None:
    claims = read_session_claims(token, secret)
    return str(claims["user_id"]) if claims else None


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
