"""Workout programming + progressive overload. Deterministic so exercises always exist in the library."""

from __future__ import annotations

import json
from typing import Any

from sqlmodel import Session, select

from ..data.exercises import EXERCISES, available_for
from ..llm import get_llm
from ..models import User, WorkoutPlan, WorkoutSession
from ..targets import age_band
from .persona import system_prompt

SCHEDULE = {
    1: ["Wed"], 2: ["Mon", "Thu"], 3: ["Mon", "Wed", "Fri"], 4: ["Mon", "Tue", "Thu", "Fri"],
    5: ["Mon", "Tue", "Wed", "Fri", "Sat"], 6: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
}

SPLITS = {
    1: ["Full Body A"], 2: ["Full Body A", "Full Body B"], 3: ["Full Body A", "Full Body B", "Full Body A"],
    4: ["Upper A", "Lower A", "Upper B", "Lower B"],
    5: ["Push", "Pull", "Legs", "Upper A", "Lower A"],
    6: ["Push", "Pull", "Legs", "Push", "Pull", "Legs"],
}

# "pattern" or "pattern:muscle" (muscle filter for isolation work)
FOCUS_PATTERNS = {
    "Full Body": ["squat", "horizontal_push", "horizontal_pull", "hinge", "vertical_push", "core"],
    "Upper": ["horizontal_push", "vertical_pull", "vertical_push", "horizontal_pull", "isolation:biceps", "isolation:triceps"],
    "Lower": ["squat", "hinge", "lunge", "core"],
    "Push": ["horizontal_push", "vertical_push", "horizontal_push", "isolation:side delts", "isolation:triceps"],
    "Pull": ["vertical_pull", "horizontal_pull", "hinge", "isolation:biceps"],
    "Legs": ["squat", "hinge", "lunge", "squat", "core"],
    # Older adults: every session gets balance work
    "Strength & Balance": ["squat", "horizontal_push", "horizontal_pull", "lunge", "hinge", "balance", "core"],
    # Kids: movement games + basic bodyweight skills
    "Play & Move": ["play", "squat", "horizontal_push", "play", "hinge", "core", "play"],
}

FALLBACK_PATTERN = {"vertical_pull": "horizontal_pull", "lunge": "squat"}
LOWER = {"squat", "hinge", "lunge"}


# Gentler variants listed first for older adults
SENIOR_PREFER = ["sit_to_stand", "wall_push_up", "dumbbell_row", "leg_press", "lat_pulldown", "step_up", "glute_bridge",
                 "dumbbell_shoulder_press"]


def _pick(pool: dict[str, dict], token: str, variant: int, used: set[str], prefer: list[str] | None = None) -> str | None:
    pattern, _, muscle = token.partition(":")
    opts = [k for k, v in pool.items() if v["pattern"] == pattern and k not in used
            and (not muscle or muscle in v["muscles"])]
    if prefer:
        opts.sort(key=lambda k: prefer.index(k) if k in prefer else len(prefer))
    if not opts and pattern in FALLBACK_PATTERN:
        return _pick(pool, FALLBACK_PATTERN[pattern], variant, used, prefer)
    if not opts:
        return None
    return opts[variant % len(opts)]


def _labels(n: int, band: str) -> list[str]:
    if band == "child":
        return ["Play & Move"] * n
    if band == "senior":
        return ["Strength & Balance"] * n
    return SPLITS[n]


def build_plan(user: User) -> dict[str, Any]:
    band = age_band(user.age)
    n = max(1, min(6, user.training_days_per_week))
    if band == "senior":
        n = min(n, 4)  # recovery takes longer; walk on other days
    equipment = "bodyweight" if band == "child" else user.equipment
    pool = available_for(equipment, band)
    sets = {"beginner": 3, "intermediate": 4, "advanced": 4}.get(user.experience, 3)
    if band in ("child", "senior"):
        sets = 2
    days = []
    for dow, label in zip(SCHEDULE[n], _labels(n, band)):
        base = label.rsplit(" ", 1)[0] if label.endswith((" A", " B")) else label
        variant = 1 if label.endswith("B") else 0
        used: set[str] = set()
        exercises = []
        for pattern in FOCUS_PATTERNS[base]:
            slug = _pick(pool, pattern, variant, used, SENIOR_PREFER if band == "senior" else None)
            if not slug:
                continue
            used.add(slug)
            ex = EXERCISES[slug]
            compound = ex["pattern"] not in ("isolation", "core")
            lo, hi = ex["rep_range"]
            if band in ("teen", "senior") and compound:
                lo, hi = max(lo, 8), max(hi, 12)  # no heavy low-rep work for growing athletes
            timed = slug in ("plank", "single_leg_balance", "bear_crawl", "animal_walks")
            exercises.append({
                "slug": slug, "name": ex["name"],
                "sets": sets if compound or band in ("child", "senior") else 3,
                "reps": f"{lo}-{hi}" + (" s" if timed else ""),
                "rest_s": 150 if compound and ex["pattern"] in LOWER else (120 if compound else 60),
            })
        days.append({"day": dow, "focus": label, "exercises": exercises})
    name = {1: "Full Body", 2: "Full Body", 3: "Full Body", 4: "Upper/Lower", 5: "PPL + Upper/Lower",
            6: "Push/Pull/Legs"}[n]
    if band in ("child", "senior"):
        name = _labels(1, band)[0]
    notes = ("Progression rule: when you hit the top of the rep range on every set, add weight next time "
             "(+5 lb / 2.5 kg upper body, +10 lb / 5 kg lower body). Leave 1-2 reps in the tank on most sets.")
    if user.goal == "lose" and band in ("adult", "senior"):
        notes += " On a cut, the goal is to keep your strength, not set PRs every week."
    if band == "child":
        notes = ("Move like it's a game! Do each one, rest when you need to, and have a grown-up nearby. "
                 "Try to get 60 minutes of active play every day: sports, biking, running around all count.")
    elif band == "teen":
        notes += " Technique first: keep loads where every rep looks clean. No one-rep maxes."
    elif band == "senior":
        notes = ("Warm up 5-10 minutes first. Hold onto something sturdy for balance work. Add reps before adding weight, "
                 "and stop if anything hurts (soreness is fine, sharp pain isn't). Walk on non-training days. "
                 "Check with your doctor before starting if you have heart, joint or balance conditions.")
    return {"name": f"{name} ({n}x/week)", "days": days, "notes": notes}


def create_plan(session: Session, user: User) -> WorkoutPlan:
    for old in session.exec(select(WorkoutPlan).where(WorkoutPlan.user_id == user.id, WorkoutPlan.active == True)):  # noqa: E712
        old.active = False
        session.add(old)
    p = build_plan(user)
    plan = WorkoutPlan(user_id=user.id, name=p["name"], days=p["days"], notes=p["notes"])
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan


def progression(session: Session, user: User, exercises: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for ex in exercises:
        slug = ex.get("slug")
        lib = EXERCISES.get(slug)
        sets = ex.get("sets") or []
        if not lib or not sets:
            continue
        lo, hi = lib["rep_range"]
        reps = [int(s.get("reps", 0)) for s in sets]
        weight_kg = max(float(s.get("weight_kg") or 0) for s in sets)
        imperial = user.units == "imperial"
        unit = "lb" if imperial else "kg"
        # Work in the user's unit so suggestions land on real plate jumps (5/10 lb or 2.5/5 kg)
        weight = round(weight_kg * 2.20462 / 2.5) * 2.5 if imperial else weight_kg
        step = (10.0 if imperial else 5.0) if lib["pattern"] in LOWER else (5.0 if imperial else 2.5)
        if lib["equipment"] == "bodyweight" or weight_kg == 0:
            if all(r >= hi for r in reps):
                tip = f"All sets at {hi}+. Make it harder: slower tempo (3 s down) or add a set."
            else:
                tip = f"Aim to add 1 rep per set next time (target {hi})."
        elif all(r >= hi for r in reps):
            tip = f"Every set hit {hi}. Next time: {weight + step:g} {unit}."
        elif any(r < lo for r in reps):
            tip = f"Some sets fell below {lo}. Stay at {weight:g} {unit} (or drop to {max(weight - step, 0):g}) and own the range."
        else:
            tip = f"Stay at {weight:g} {unit} and add reps until every set hits {hi}."
        volume = sum(int(s.get("reps", 0)) * float(s.get("weight_kg") or 0) for s in sets)
        # previous best volume for this exercise
        prev_best = 0.0
        for ws in session.exec(select(WorkoutSession).where(WorkoutSession.user_id == user.id)):
            for pe in ws.exercises:
                if pe.get("slug") == slug:
                    v = sum(int(s.get("reps", 0)) * float(s.get("weight_kg") or 0) for s in pe.get("sets", []))
                    prev_best = max(prev_best, v)
        out.append({"slug": slug, "name": lib["name"], "next_time": tip,
                    "volume_kg": round(volume), "volume_pr": volume > prev_best > 0})
    return out


def session_feedback(user: User, focus: str, prog: list[dict[str, Any]]) -> str:
    prs = [p["name"] for p in prog if p["volume_pr"]]
    fallback = (f"{focus or 'Session'} logged. " + (f"Volume PR on {', '.join(prs)}. " if prs else "")
                + " ".join(f"{p['name']}: {p['next_time']}" for p in prog[:3]))
    llm = get_llm()
    if llm is None:
        return fallback
    try:
        return llm.text(system=system_prompt(user), messages=[{"role": "user", "content":
                        f"I just finished {focus}. Progression analysis: {json.dumps(prog)}. "
                        "Give me a 2-3 sentence post-workout debrief and remind me to eat protein."}],
                        max_tokens=250)
    except Exception:
        return fallback
