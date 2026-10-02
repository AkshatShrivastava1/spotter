"""All-ages behavior: kids/teens never get calorie or weight coaching; seniors get balance-focused plans."""

from datetime import datetime, timezone

from sqlmodel import Session

from app.coach.nudges import evaluate_user
from app.db import engine
from app.models import User
from tests.conftest import ONBOARD

KID = {**ONBOARD, "name": "Aarav", "age": 8, "height_cm": 128, "weight_kg": 26, "goal": "lose", "coach_tone": "drill"}
TEEN = {**ONBOARD, "name": "Maya", "age": 15, "sex": "female", "height_cm": 160, "weight_kg": 52, "goal": "lose"}
SENIOR = {**ONBOARD, "name": "Ram", "age": 72, "height_cm": 168, "weight_kg": 70, "goal": "lose"}


def _make(client, body):
    r = client.post("/users", json=body)
    assert r.status_code == 200, r.text
    uid = r.json()["user"]["id"]
    return uid, {"X-User-Id": str(uid)}


def test_child_requires_guardian(client):
    r = client.post("/users", json=KID)
    assert r.status_code == 422
    assert "guardian" in r.text


def test_child_account_is_habit_mode(client):
    uid, h = _make(client, {**KID, "guardian_name": "Priya (mom)", "guardian_consent": True})
    me = client.get("/users/me", headers=h).json()
    assert me["age_band"] == "child"
    assert me["goal"] == "maintain" and me["coach_tone"] == "gentle"
    today = client.get("/today", headers=h).json()
    assert today["show_calories"] is False
    plan = client.get("/workouts/plan", headers=h).json()
    slugs = {e["slug"] for d in plan["days"] for e in d["exercises"]}
    assert "bear_crawl" in slugs and "deadlift" not in slugs and "bench_press" not in slugs


def test_teen_meal_feedback_has_no_calorie_talk_and_no_recovery(client):
    uid, h = _make(client, TEEN)
    assert client.get("/users/me", headers=h).json()["goal"] == "maintain"
    big = [{"name": "pizza", "quantity": "6 slices", "kcal": 3500, "protein_g": 70, "carbs_g": 400, "fat_g": 150}]
    r = client.post("/meals", json={"meal_type": "dinner", "items": big}, headers=h).json()
    assert "kcal" not in r["feedback"].lower() and "calorie" not in r["feedback"].lower()
    assert r["recovery"] is None
    kinds = [n["kind"] for n in client.get("/notifications", headers=h).json()]
    assert "over_budget" not in kinds
    # can't change goal to a cut
    client.patch("/users/me", json={"goal": "lose"}, headers=h)
    assert client.get("/users/me", headers=h).json()["goal"] == "maintain"


def test_teen_no_weigh_in_nudge_or_photos(client):
    uid, h = _make(client, TEEN)
    with Session(engine) as s:
        u = s.get(User, uid)
        today = datetime.now(timezone.utc).date()
        out = evaluate_user(s, u, datetime(today.year, today.month, today.day, 12, 15, tzinfo=timezone.utc), use_llm=False)
        assert [n.kind for n in out] == ["morning_brief"]
        assert "kcal" not in out[0].body
    r = client.post("/progress-photos", files={"file": ("f.png", b"x", "image/png")}, headers=h)
    assert r.status_code == 403


def test_senior_plan_is_gentle(client):
    uid, h = _make(client, {**SENIOR, "training_days_per_week": 6})
    plan = client.get("/workouts/plan", headers=h).json()
    assert len(plan["days"]) <= 4
    slugs = [e["slug"] for d in plan["days"] for e in d["exercises"]]
    assert "single_leg_balance" in slugs
    assert not {"deadlift", "barbell_back_squat", "pull_up"} & set(slugs)
    me = client.get("/users/me", headers=h).json()
    assert me["age_band"] == "senior"
    assert me["target_protein_g"] == round(1.3 * 70)
