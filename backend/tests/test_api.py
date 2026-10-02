from datetime import datetime, timedelta, timezone

from sqlmodel import Session

from app.coach.checkin import recommend_adjustment
from app.coach.context import get_daily_log, local_today
from app.coach.nudges import evaluate_user
from app.coach.nutrition import heuristic_parse
from app.db import engine
from app.models import Meal, User
from app.targets import compute_targets


def test_targets_reasonable():
    t = compute_targets(sex="male", age=22, height_cm=178, weight_kg=80, goal="lose", activity_level="moderate")
    assert 2000 < t.kcal < 2600
    assert t.protein_g == 160
    assert t.carbs_g > 100


def test_targets_floor():
    t = compute_targets(sex="female", age=60, height_cm=150, weight_kg=45, goal="lose", activity_level="sedentary")
    assert t.kcal >= 1200


def test_heuristic_parse_indian_meal():
    out = heuristic_parse("2 rotis, 1 cup dal and 150g paneer")
    names = [i["name"] for i in out["items"]]
    assert names == ["roti", "dal", "paneer"]
    roti = out["items"][0]
    assert roti["kcal"] == 240
    paneer = out["items"][2]
    assert round(paneer["protein_g"]) == 27


def test_heuristic_parse_unknown_asks():
    out = heuristic_parse("2 eggs and some mystery casserole")
    assert len(out["items"]) == 1
    assert "mystery casserole" in out["clarifying_question"]


def test_onboarding_creates_targets_and_plan(client, user):
    u = user["data"]["user"]
    assert u["target_protein_g"] == 160
    plan = client.get("/workouts/plan", headers=user["h"]).json()
    assert len(plan["days"]) == 4
    assert plan["days"][0]["focus"] == "Upper A"
    assert all(e["slug"] for d in plan["days"] for e in d["exercises"])


def test_log_meal_feedback_and_today(client, user):
    parsed = client.post("/food/parse", json={"text": "2 roti and 1 cup dal"}, headers=user["h"]).json()
    assert parsed["totals"]["kcal"] == 470
    r = client.post("/meals", json={"meal_type": "lunch", "items": parsed["items"]}, headers=user["h"])
    assert r.status_code == 200, r.text
    body = r.json()
    assert "Protein was light" in body["feedback"]
    today = client.get("/today", headers=user["h"]).json()
    assert today["eaten"]["kcal"] == 470
    assert today["meal_types_logged"] == ["lunch"]


def test_overage_triggers_recovery(client, user):
    big = [{"name": "biryani", "quantity": "5 plates", "kcal": 3000, "protein_g": 100, "carbs_g": 350, "fat_g": 110}]
    r = client.post("/meals", json={"meal_type": "dinner", "items": big}, headers=user["h"]).json()
    assert r["recovery"]["over_kcal"] > 0
    assert r["recovery"]["trim_next_days_kcal"] > 0
    notes = client.get("/notifications", headers=user["h"]).json()
    assert notes[0]["kind"] == "over_budget"
    # tomorrow's target is trimmed
    with Session(engine) as s:
        u = s.get(User, user["id"])
        tomorrow = get_daily_log(s, u, local_today(u) + timedelta(days=1))
        assert tomorrow.kcal_adjustment == -r["recovery"]["trim_next_days_kcal"]


def test_meal_ideas_respect_diet(client, user):
    ideas = client.get("/meal-ideas", headers=user["h"]).json()
    assert ideas["question"] is None
    assert ideas["ideas"]
    text = " ".join(i["items"] for i in ideas["ideas"])
    assert "chicken" not in text and "fish" not in text  # eggetarian


def test_meal_ideas_asks_when_no_home_foods(client):
    from tests.conftest import ONBOARD
    r = client.post("/users", json={**ONBOARD, "home_foods": []}).json()
    out = client.get("/meal-ideas", headers={"X-User-Id": str(r["user"]["id"])}).json()
    assert "what do you usually cook" in out["question"].lower()


def test_water_steps_weight_trend(client, user):
    client.post("/track/water", json={"amount": 500}, headers=user["h"])
    assert client.post("/track/water", json={"amount": 250}, headers=user["h"]).json()["water_ml"] == 750
    assert client.post("/track/steps", json={"amount": 4200}, headers=user["h"]).json()["steps"] == 4200
    # seed two weeks of weights: 80 -> 79.4 avg
    with Session(engine) as s:
        u = s.get(User, user["id"])
        today = local_today(u)
        for i in range(14):
            log = get_daily_log(s, u, today - timedelta(days=i))
            log.weight_kg = 79.4 if i < 7 else 80.0
            s.add(log)
        s.commit()
    t = client.get("/weight/trend", headers=user["h"]).json()
    assert t["this_week_avg"] == 79.4 and t["last_week_avg"] == 80.0
    assert t["change_kg"] == -0.6
    assert "pace" in t["verdict"]


def test_weekly_checkin_adjusts_when_stalled(client, user):
    with Session(engine) as s:
        u = s.get(User, user["id"])
        today = local_today(u)
        for i in range(14):
            log = get_daily_log(s, u, today - timedelta(days=i))
            log.weight_kg = 80.0
            s.add(log)
            for mt in ("lunch", "dinner"):
                s.add(Meal(user_id=u.id, day=today - timedelta(days=i), meal_type=mt, kcal=1100, protein_g=80))
        s.commit()
        before = u.target_kcal
    status = client.get("/checkin", headers=user["h"]).json()
    assert status["due"] is True
    r = client.post("/checkin", json={"answers": {"energy": 3, "hunger": 3}}, headers=user["h"]).json()
    assert r["kcal_change"] == -150
    assert client.get("/users/me", headers=user["h"]).json()["target_kcal"] == before - 150
    assert "176.4" in r["coach_review"]
    assert client.get("/checkin", headers=user["h"]).json()["due"] is False


def test_adjustment_requires_adherence():
    u = User(name="x", goal="lose")
    assert recommend_adjustment(u, {"change_pct": 0.0}, {"days_logged": 3}) == 0
    assert recommend_adjustment(u, {"change_pct": -1.5}, {"days_logged": 6}) == 150


def test_workout_session_progression(client, user):
    sets = [{"reps": 8, "weight_kg": 60}] * 3
    r1 = client.post("/workouts/sessions", json={"focus": "Upper A", "exercises": [
        {"slug": "bench_press", "sets": sets}]}, headers=user["h"]).json()
    assert "Next time: 137.5 lb" in r1["progression"][0]["next_time"]
    r2 = client.post("/workouts/sessions", json={"focus": "Upper A", "exercises": [
        {"slug": "bench_press", "sets": [{"reps": 8, "weight_kg": 62.5}] * 3}]}, headers=user["h"]).json()
    assert r2["progression"][0]["volume_pr"] is True
    last = client.get("/workouts/last/bench_press", headers=user["h"]).json()
    assert last["sets"][0]["weight_kg"] == 62.5


def _at_local(hour: int, minute: int = 0) -> datetime:
    # America/New_York in October = UTC-4
    today = datetime.now(timezone.utc).date()
    return datetime(today.year, today.month, today.day, hour + 4, minute, tzinfo=timezone.utc)


def test_nudges_fire_in_window_once(client, user):
    with Session(engine) as s:
        u = s.get(User, user["id"])
        first = evaluate_user(s, u, _at_local(7, 40), use_llm=False)
        assert [n.kind for n in first] == ["weigh_in"]
        second = evaluate_user(s, u, _at_local(8, 10), use_llm=False)
        assert [n.kind for n in second] == ["morning_brief"]
        third = evaluate_user(s, u, _at_local(8, 30), use_llm=False)
        assert third == []  # nothing else due; no repeats


def test_lunch_missing_nudge(client, user):
    with Session(engine) as s:
        u = s.get(User, user["id"])
        out = evaluate_user(s, u, _at_local(14, 30), use_llm=False)
        kinds = [n.kind for n in out]
        assert kinds and kinds[0] in ("lunch_missing", "ghosting")


def test_chat_offline_mode(client, user):
    r = client.post("/coach/chat", json={"message": "what should I eat for dinner?"}, headers=user["h"]).json()
    assert "kcal" in r["reply"]
    msgs = client.get("/coach/messages", headers=user["h"]).json()
    assert [m["role"] for m in msgs] == ["user", "coach"]


def test_progress_photo_roundtrip(client, user, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 100
    r = client.post("/progress-photos", files={"file": ("f.png", png, "image/png")}, data={"pose": "side"},
                    headers=user["h"]).json()
    img = client.get(f"/progress-photos/{r['id']}/image", headers=user["h"])
    assert img.status_code == 200 and img.content == png
    other = client.get(f"/progress-photos/{r['id']}/image", headers={"X-User-Id": "999999"})
    assert other.status_code == 404
