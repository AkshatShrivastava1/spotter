"""Email + password accounts with signed tokens.

Passwords are hashed with scrypt (Python stdlib, memory-hard). Tokens are HS256 JWTs signed
with SPOTTER_JWT_SECRET. Nothing here needs a third-party auth service.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import secrets
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

import jwt

from .config import get_settings

log = logging.getLogger(__name__)

_N, _R, _P = 2**14, 8, 1
_TOKEN_DAYS = 30
_dev_secret = secrets.token_urlsafe(32)


def _secret() -> str:
    s = get_settings().jwt_secret
    if not s:
        log.warning("SPOTTER_JWT_SECRET not set; using a random dev secret (logins reset on restart)")
        return _dev_secret
    return s


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P)
    b64 = lambda b: base64.b64encode(b).decode()  # noqa: E731
    return f"scrypt${_N}${_R}${_P}${b64(salt)}${b64(digest)}"


def verify_password(password: str, stored: str | None) -> bool:
    if not stored:
        return False
    try:
        _algo, n, r, p, salt, digest = stored.split("$")
        check = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt), n=int(n), r=int(r), p=int(p))
        return hmac.compare_digest(check, base64.b64decode(digest))
    except (ValueError, TypeError):
        return False


def create_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "iat": now, "exp": now + timedelta(days=_TOKEN_DAYS)}
    return jwt.encode(payload, _secret(), algorithm="HS256")


def user_id_from_token(token: str) -> int | None:
    try:
        return int(jwt.decode(token, _secret(), algorithms=["HS256"])["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


# ---- brute-force protection: max 5 failed logins per email per 15 minutes (per server process) ----
_WINDOW_S, _MAX_FAILS = 15 * 60, 5
_fails: dict[str, deque[float]] = defaultdict(deque)


def too_many_attempts(email: str) -> bool:
    q = _fails[email]
    while q and time.monotonic() - q[0] > _WINDOW_S:
        q.popleft()
    return len(q) >= _MAX_FAILS


def record_failure(email: str) -> None:
    _fails[email].append(time.monotonic())


def clear_failures(email: str) -> None:
    _fails.pop(email, None)
