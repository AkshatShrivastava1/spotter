import os
import tempfile
import uuid

_tmp = tempfile.mkdtemp()
# Default: throwaway SQLite. Set TEST_DATABASE_URL to run the same suite against Postgres (CI does).
os.environ["SPOTTER_DATABASE_URL"] = os.getenv("TEST_DATABASE_URL") or f"sqlite:///{_tmp}/test.db"
os.environ["SPOTTER_UPLOADS_DIR"] = f"{_tmp}/uploads"
os.environ["SPOTTER_SCHEDULER_ENABLED"] = "false"
os.environ["SPOTTER_EXPO_PUSH_ENABLED"] = "false"
os.environ["SPOTTER_LLM_PROVIDER"] = "mock"
os.environ["SPOTTER_JWT_SECRET"] = "test-secret-that-is-at-least-32-bytes-long"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import SQLModel  # noqa: E402

from app import models  # noqa: E402, F401
from app.db import engine  # noqa: E402
from app.llm import set_llm_for_tests  # noqa: E402
from app.main import app  # noqa: E402

set_llm_for_tests(None)
# Start every run from an empty schema (matters when pointing at a reused Postgres database).
SQLModel.metadata.drop_all(engine)
SQLModel.metadata.create_all(engine)

ONBOARD = {
    "name": "Akshat", "timezone": "America/New_York", "sex": "male", "age": 22, "height_cm": 178,
    "weight_kg": 80, "goal": "lose", "activity_level": "moderate", "diet_type": "eggetarian",
    "home_foods": ["dal", "roti", "eggs", "paneer bhurji", "rice", "curd"], "equipment": "full_gym",
    "training_days_per_week": 4,
}


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def signup(client, body: dict | None = None, *, expect: int = 200):
    """Create an account. Returns (user_id, auth headers, response json)."""
    body = {**(body or ONBOARD)}
    body.setdefault("email", f"user-{uuid.uuid4().hex[:10]}@example.com")
    body.setdefault("password", "correct-horse-battery")
    r = client.post("/auth/signup", json=body)
    assert r.status_code == expect, r.text
    if expect != 200:
        return None, None, r.json()
    data = r.json()
    return data["user"]["id"], {"Authorization": f"Bearer {data['access_token']}"}, data


@pytest.fixture()
def user(client):
    uid, h, data = signup(client)
    return {"id": uid, "h": h, "data": data}
