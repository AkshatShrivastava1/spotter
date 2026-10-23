"""Week 4: real accounts instead of trusting an X-User-Id header."""

import jwt
from sqlalchemy import create_engine, inspect, text

from app import auth
from tests.conftest import ONBOARD, signup


def test_signup_returns_token_and_never_leaks_the_hash(client):
    uid, h, data = signup(client, {**ONBOARD, "email": "Akshat@Example.com"})
    assert data["access_token"]
    assert "password_hash" not in data["user"]
    me = client.get("/users/me", headers=h).json()
    assert me["id"] == uid and me["email"] == "akshat@example.com"
    assert "password_hash" not in me


def test_duplicate_email_is_rejected(client):
    signup(client, {**ONBOARD, "email": "dup@example.com"})
    _uid, _h, body = signup(client, {**ONBOARD, "email": "DUP@example.com"}, expect=409)
    assert "already exists" in body["detail"]


def test_weak_input_is_rejected(client):
    signup(client, {**ONBOARD, "email": "not-an-email"}, expect=422)
    signup(client, {**ONBOARD, "password": "short"}, expect=422)


def test_login_works_and_wrong_password_fails(client):
    signup(client, {**ONBOARD, "email": "login@example.com", "password": "correct-horse-battery"})
    ok = client.post("/auth/login", json={"email": " LOGIN@example.com ", "password": "correct-horse-battery"})
    assert ok.status_code == 200
    h = {"Authorization": f"Bearer {ok.json()['access_token']}"}
    assert client.get("/today", headers=h).status_code == 200
    bad = client.post("/auth/login", json={"email": "login@example.com", "password": "wrong-password"})
    assert bad.status_code == 401
    unknown = client.post("/auth/login", json={"email": "nobody@example.com", "password": "whatever-123"})
    assert unknown.status_code == 401 and unknown.json()["detail"] == bad.json()["detail"]  # no account probing


def test_repeated_failures_are_throttled(client):
    signup(client, {**ONBOARD, "email": "brute@example.com"})
    for _ in range(5):
        client.post("/auth/login", json={"email": "brute@example.com", "password": "guess-guess"})
    r = client.post("/auth/login", json={"email": "brute@example.com", "password": "correct-horse-battery"})
    assert r.status_code == 429


def test_endpoints_require_a_valid_token(client, user):
    assert client.get("/today").status_code == 401
    assert client.get("/today", headers={"X-User-Id": str(user["id"])}).status_code == 401  # old header is dead
    assert client.get("/today", headers={"Authorization": "Bearer garbage"}).status_code == 401
    forged = jwt.encode({"sub": str(user["id"])}, "some-other-secret-that-is-32-bytes-x", algorithm="HS256")
    assert client.get("/today", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_password_hashing():
    h = auth.hash_password("hunter22-hunter22")
    assert h.startswith("scrypt$") and "hunter22" not in h
    assert auth.verify_password("hunter22-hunter22", h)
    assert not auth.verify_password("hunter22-hunter23", h)
    assert not auth.verify_password("anything", None)
    assert auth.hash_password("same") != auth.hash_password("same")  # salted


def test_old_database_gets_new_columns(tmp_path, monkeypatch):
    """A database created before accounts existed is upgraded in place on startup."""
    from app import db

    old = create_engine(f"sqlite:///{tmp_path}/old.db")
    with old.begin() as c:
        c.execute(text('CREATE TABLE "user" (id INTEGER PRIMARY KEY, name VARCHAR NOT NULL)'))
        c.execute(text("""INSERT INTO "user" (id, name) VALUES (1, 'Old User')"""))
    monkeypatch.setattr(db, "engine", old)
    db._add_missing_columns()
    cols = {c["name"] for c in inspect(old).get_columns("user")}
    assert {"email", "password_hash", "units", "guardian_name"} <= cols
    with old.connect() as c:
        assert c.execute(text('SELECT name FROM "user"')).scalar() == "Old User"
