"""Exercise the LLM code paths with a fake model so they can't silently break."""

from app.llm import set_llm_for_tests


class FakeLLM:
    def __init__(self):
        self.calls = []

    def json(self, *, system, prompt, schema, images=None, role="parse", max_tokens=1500):
        self.calls.append(("json", prompt))
        if "new_facts" in str(schema):
            return {"new_facts": ["trains in the morning"]}
        return {"items": [{"name": "dal (with ghee tadka)", "quantity": "1 bowl", "kcal": 260, "protein_g": 12,
                           "carbs_g": 30, "fat_g": 10, "fiber_g": 8, "confidence": "medium"}],
                "clarifying_question": ""}

    def text(self, *, system, messages, role="coach", max_tokens=700):
        assert "Spotter" in system
        self.calls.append(("text", messages[-1]["content"]))
        return "COACH: eat protein next."


def test_llm_paths(client, user):
    fake = FakeLLM()
    set_llm_for_tests(fake)
    try:
        p = client.post("/food/photo", files={"file": ("m.jpg", b"\xff\xd8fake", "image/jpeg")},
                        headers=user["h"]).json()
        assert p["items"][0]["name"].startswith("dal")
        r = client.post("/meals", json={"meal_type": "lunch", "items": p["items"]}, headers=user["h"]).json()
        assert r["feedback"] == "COACH: eat protein next."
        c = client.post("/coach/chat", json={"message": "I train at 6am"}, headers=user["h"]).json()
        assert c["reply"].startswith("COACH")
        me = client.get("/users/me", headers=user["h"]).json()
        assert "trains in the morning" in me["coach_notes"]
        ideas = client.get("/meal-ideas", headers=user["h"]).json()
        assert ideas["intro"].startswith("COACH")
    finally:
        set_llm_for_tests(None)
