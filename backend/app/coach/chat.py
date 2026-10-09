"""Free-form conversation with the coach, with memory of durable facts."""

from __future__ import annotations

from sqlmodel import Session, select

from ..llm import get_llm
from ..models import CoachMessage, User
from .feedback import candidate_meals, meal_ideas
from .persona import system_prompt

NOTES_SCHEMA = {
    "type": "object",
    "properties": {"new_facts": {"type": "array", "items": {"type": "string"},
                                 "description": "Durable facts about the user's habits, schedule, preferences, "
                                                "constraints or injuries worth remembering for coaching. "
                                                "Empty if none. Do not repeat known facts."}},
    "required": ["new_facts"],
}


def _offline_intents(user: User, state: dict, t: str, youth: bool) -> str | None:
    """Canned-but-useful answers for the app's own quick prompts, so offline mode isn't a dead end."""
    rem = state["remaining"]
    if "meal prep" in t or "prep" in t.split():
        if not user.home_foods:
            return "Tell me what you usually cook at home first (Settings → Home staples) and I'll build a prep plan around it."
        plates = candidate_meals(user, 550, 40, limit=3)
        lines = ["Batch-cook 2 things on Sunday and Wednesday, portion into containers, and lunches are solved:"]
        lines += [f"- {p['items']}" + ("" if youth else f" (~{p['kcal']} kcal, {p['protein_g']} g protein)") for p in plates]
        lines.append("Cook the protein and the carb in bulk, keep veg fresh, and you'll have 6-8 meals ready.")
        return "\n".join(lines)
    if any(w in t for w in ("craving", "crave", "junk", "sweet tooth", "chocolate", "pizza")):
        if youth:
            return ("Totally normal! Have a small portion with a real meal instead of on an empty stomach, "
                    "and drink a glass of water first. Fruit, yogurt or a handful of nuts work great too.")
        budget = max(rem["kcal"], 0)
        return (f"Cravings happen. You have {budget} kcal left today. Options: have a single portion "
                "(not the family pack) after a protein-heavy meal, or swap: Greek yogurt with honey, a protein bar, "
                "air-popped popcorn, or dark chocolate squares. Drink water and wait 10 minutes first; "
                "half the time the craving fades.")
    if any(w in t for w in ("bad day", "messed up", "ate too much", "overate", "binge", "fix", "went over")):
        if youth:
            return "No day is 'bad'. Tomorrow, just aim for water, a fruit or veggie at each meal, and an hour of play."
        over = -rem["kcal"]
        if over > 0:
            return (f"You're {over} kcal over today. Don't skip meals or do punishment cardio. "
                    "Finish today with lean protein and veg, drink water, take a 20-30 minute walk, "
                    "and I'll trim the next 2 days slightly. One day doesn't move the weekly average much.")
        return ("One off day doesn't erase a good week. Next meal: protein first (eggs, dal, chicken, paneer, yogurt), "
                "add veg, drink water, and go for a walk. Log it all, even the messy stuff, so I can adjust.")
    if any(w in t for w in ("water", "hydrat")):
        return f"{state['water_ml']} of {state['target']['water_ml']} ml so far. Two glasses now, then one with every meal."
    if any(w in t for w in ("protein",)) and not youth:
        return (f"{state['eaten']['protein_g']} of {state['target']['protein_g']} g protein so far. Easy adds: "
                "eggs, Greek yogurt or curd, dal, paneer, chicken, tofu, or a scoop of whey.")
    return None


def _fallback_reply(user: User, state: dict, text: str) -> str:
    t = text.lower()
    rem = state["remaining"]
    youth = not state.get("show_calories", True)
    special = _offline_intents(user, state, t, youth)
    if special:
        return special
    if any(w in t for w in ("eat", "meal", "hungry", "dinner", "lunch", "breakfast", "snack", "cook")):
        ideas = meal_ideas(user, state)
        if ideas["question"]:
            return ideas["question"]
        lines = [ideas["intro"]] + [
            f"- {i['items']}" + (f" (~{i['kcal']} kcal, {i['protein_g']} g P)" if "kcal" in i else "") for i in ideas["ideas"]]
        return "\n".join(lines)
    if any(w in t for w in ("how am i", "status", "left", "remaining", "today")):
        if not state.get("show_calories", True):
            return (f"So far: {state['eaten']['protein_g']} g protein, {state['water_ml']} ml water, "
                    f"{state['steps']:,} steps. Keep it up: grab some water and go play for a bit!")
        return (f"{state['eaten']['kcal']}/{state['target']['kcal']} kcal, "
                f"{state['eaten']['protein_g']}/{state['target']['protein_g']} g protein, "
                f"{state['water_ml']}/{state['target']['water_ml']} ml water, {state['steps']:,} steps. "
                f"{max(rem['kcal'], 0)} kcal left: make the next meal protein-first.")
    return ("I'm running in offline mode (no AI key on the server), so I can answer 'what should I eat', "
            "'how am I doing today', and log food. Add an API key for full coaching chat.")


def chat(session: Session, user: User, state: dict, text: str) -> str:
    session.add(CoachMessage(user_id=user.id, role="user", content=text))
    session.commit()
    llm = get_llm()
    if llm is None:
        reply = _fallback_reply(user, state, text)
    else:
        history = list(session.exec(
            select(CoachMessage).where(CoachMessage.user_id == user.id)
            .order_by(CoachMessage.created_at.desc()).limit(20)))[::-1]
        msgs: list[dict[str, str]] = []
        for m in history:
            role = "assistant" if m.role == "coach" else "user"
            if msgs and msgs[-1]["role"] == role:
                msgs[-1]["content"] += "\n" + m.content
            else:
                msgs.append({"role": role, "content": m.content})
        if msgs and msgs[0]["role"] == "assistant":
            msgs.insert(0, {"role": "user", "content": "(conversation start)"})
        reply = llm.text(system=system_prompt(user, state), messages=msgs)
        _learn(session, user, text, llm)
    session.add(CoachMessage(user_id=user.id, role="coach", content=reply))
    session.commit()
    return reply


def _learn(session: Session, user: User, text: str, llm) -> None:
    try:
        out = llm.json(system="Extract durable coaching facts.",
                       prompt=f"Known facts: {user.coach_notes}\nUser said: {text}", schema=NOTES_SCHEMA)
        new = [f for f in out.get("new_facts", []) if f and f not in user.coach_notes]
        if new:
            user.coach_notes = (user.coach_notes + new)[-30:]
            session.add(user)
            session.commit()
    except Exception:
        pass
