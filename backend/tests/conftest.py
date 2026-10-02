import os
import tempfile

_tmp = tempfile.mkdtemp()
os.environ["SPOTTER_DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["SPOTTER_SCHEDULER_ENABLED"] = "false"
os.environ["SPOTTER_EXPO_PUSH_ENABLED"] = "false"
os.environ["SPOTTER_LLM_PROVIDER"] = "mock"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.llm import set_llm_for_tests  # noqa: E402
from app.main import app  # noqa: E402

set_llm_for_tests(None)

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


@pytest.fixture()
def user(client):
    r = client.post("/users", json=ONBOARD)
    assert r.status_code == 200, r.text
    uid = r.json()["user"]["id"]
    return {"id": uid, "h": {"X-User-Id": str(uid)}, "data": r.json()}
