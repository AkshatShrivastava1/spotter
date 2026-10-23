"""Week 2: fixes from the first real test run."""

from app.coach.feedback import candidate_meals
from app.coach.nutrition import heuristic_parse
from app.models import User
from tests.conftest import ONBOARD, signup


def test_mutton_curry_is_recognized():
    out = heuristic_parse("a bowl of mutton curry w small pieces of boned mutton, kidney pieces")
    names = [i["name"] for i in out["items"]]
    assert names == ["mutton curry", "mutton kidney"]
    # "small pieces" describes the meat, not the portion, so the bowl isn't shrunk
    assert out["items"][0]["kcal"] == 420
    assert out["clarifying_question"] == ""


def test_kidney_beans_still_mean_rajma():
    out = heuristic_parse("1 cup kidney beans")
    assert [i["name"] for i in out["items"]] == ["rajma"]


def test_size_words_scale_portion():
    out = heuristic_parse("small bowl of keema")
    assert out["items"][0]["kcal"] == round(380 * 0.7)


def test_protein_in_gravy_becomes_curry():
    assert heuristic_parse("chicken chettinad gravy")["items"][0]["name"] == "chicken curry"
    assert heuristic_parse("grilled chicken")["items"][0]["name"] == "chicken breast"


def test_unknown_dish_gets_a_low_confidence_guess():
    out = heuristic_parse("veg chettinad gravy")
    item = out["items"][0]
    assert item["name"] == "curry (guessed)" and item["confidence"] == "low"
    assert "guessed" in out["clarifying_question"]


def test_truly_unknown_still_asks():
    out = heuristic_parse("some mystery casserole")
    assert out["items"] == [] and "couldn't size up" in out["clarifying_question"]


def test_plural_quantities():
    assert heuristic_parse("2 naan")["items"][0]["quantity"] == "2 pieces"
    assert heuristic_parse("2 cups dal")["items"][0]["quantity"] == "2 cups"


def test_meal_ideas_fit_budget_including_top_up():
    u = User(name="a", diet_type="eggetarian", home_foods=["dal", "roti", "eggs", "paneer bhurji", "curd"])
    for m in candidate_meals(u, 575, 40):
        assert m["kcal"] <= 575 * 1.05
        assert "1.5 large egg" not in m["items"]  # no half eggs


def test_vegetarian_never_gets_new_meat_dishes():
    u = User(name="a", diet_type="vegetarian", home_foods=["mutton curry", "dal", "roti"])
    text = " ".join(m["items"] for m in candidate_meals(u, 600, 40))
    assert "mutton" not in text and "keema" not in text


def test_rebuild_plan_changes_and_explains(client):
    _uid, h, _ = signup(client)
    first = client.get("/workouts/plan", headers=h).json()
    rebuilt = client.post("/workouts/plan/generate", headers=h).json()
    assert rebuilt["message"].startswith("New plan built")
    slugs = lambda p: [e["slug"] for d in p["days"] for e in d["exercises"]]  # noqa: E731
    assert slugs(first) != slugs(rebuilt)


def test_rebuild_plan_says_so_when_nothing_can_change(client):
    _uid, h, _ = signup(client, {**ONBOARD, "equipment": "bodyweight", "training_days_per_week": 3})
    msg = client.post("/workouts/plan/generate", headers=h).json()["message"]
    assert "aren't other options" in msg


def test_offline_chat_handles_quick_prompts(client):
    _uid, h, _ = signup(client)
    ask = lambda q: client.post("/coach/chat", json={"message": q}, headers=h).json()["reply"]  # noqa: E731
    assert "offline mode" not in ask("how to fix a bad day?")
    assert "Cravings happen" in ask("I'm craving junk food")
    assert "Batch-cook" in ask("Give me a meal prep plan for the week")
