"""After-meal feedback, overage recovery plans, and meal ideas.

Pattern: compute the facts deterministically, then (if an LLM is available) let the
coach persona phrase it. The deterministic text is a complete answer on its own.
"""

from __future__ import annotations

import itertools
import json
from datetime import date, timedelta
from typing import Any

from sqlmodel import Session

from ..data.foods import FOODS
from ..llm import get_llm
from ..models import User
from ..targets import KCAL_PER_STEP
from .context import get_daily_log
from .nutrition import fmt_qty
from .persona import system_prompt

MEAL_SHARE = {"breakfast": 0.25, "lunch": 0.35, "dinner": 0.30, "snack": 0.10}

MEAT = {"chicken breast", "butter chicken", "chicken curry", "fish", "tuna", "biryani", "burger"}
EGG = {"egg", "egg whites", "omelette"}
DAIRY = {"paneer", "paneer bhurji", "palak paneer", "curd", "greek yogurt", "milk", "whey protein",
         "ghee", "latte", "chai", "pizza", "butter chicken"}

PROTEIN_SOURCES = ["chicken breast", "chicken curry", "fish", "tuna", "omelette", "egg", "paneer bhurji", "palak paneer",
                   "tofu", "dal", "rajma", "chole"]
# Easy protein top-ups when a plate falls short
PROTEIN_ADDONS = ["whey protein", "greek yogurt", "egg whites", "curd"]
CARB_SOURCES = ["roti", "white rice", "brown rice", "oats", "poha", "idli", "dosa", "whole wheat bread",
                "khichdi", "banana", "apple"]
VEG_SOURCES = ["sabzi", "salad", "sambar"]


def allowed_foods(user: User) -> set[str]:
    banned: set[str] = set()
    if user.diet_type in ("vegetarian", "eggetarian", "vegan"):
        banned |= MEAT
    if user.diet_type in ("vegetarian", "vegan"):
        banned |= EGG
    if user.diet_type == "vegan":
        banned |= DAIRY
    if user.diet_type == "pescatarian":
        banned |= MEAT - {"fish", "tuna"}
    for a in user.allergies:
        banned |= {n for n in FOODS if a.lower() in n}
    return set(FOODS) - banned


# ---------- meal feedback ----------

def analyze_youth_meal(meal_type: str, meal: dict[str, float], items: list[str]) -> dict[str, Any]:
    """Kids/teens: talk about building a good plate, never about calories or 'too much'."""
    plants = any(k in " ".join(items).lower() for k in ("salad", "sabzi", "veg", "fruit", "apple", "banana", "bhindi",
                                                        "spinach", "palak", "carrot", "broccoli", "sambar", "dal", "rajma", "chole"))
    verdicts = []
    if meal["protein_g"] >= 12:
        verdicts.append(("protein_good", "Nice, that had good protein for growing muscles."))
    else:
        verdicts.append(("protein_low", "Next time add something with protein, like eggs, dal, paneer, yogurt or chicken."))
    if not plants:
        verdicts.append(("plants_missing", "Can you add a fruit or a veggie to your next meal? Aim for a colourful plate."))
    return {"verdicts": verdicts, "moves": ["Drink some water and go move for a bit today: play counts!"]}


def analyze_meal(user: User, meal_type: str, meal: dict[str, float], state: dict) -> dict[str, Any]:
    share = MEAL_SHARE.get(meal_type, 0.2)
    t = state["target"]
    rem = state["remaining"]
    verdicts = []
    if meal["protein_g"] < 0.75 * share * t["protein_g"]:
        verdicts.append(("protein_low", f"Protein was light ({meal['protein_g']:.0f} g vs ~{share * t['protein_g']:.0f} g "
                                        f"for a {meal_type})."))
    elif meal["protein_g"] >= share * t["protein_g"]:
        verdicts.append(("protein_good", f"Solid protein: {meal['protein_g']:.0f} g."))
    if meal["kcal"] > 1.35 * share * t["kcal"] and meal_type != "snack":
        verdicts.append(("kcal_high", f"That {meal_type} was big ({meal['kcal']:.0f} kcal, about "
                                      f"{share * t['kcal']:.0f} would fit the plan)."))
    if meal_type == "snack" and meal["kcal"] > 300:
        verdicts.append(("snack_big", f"{meal['kcal']:.0f} kcal is a meal, not a snack."))
    if user.goal == "lose" and meal["fat_g"] * 9 > 0.45 * max(meal["kcal"], 1):
        verdicts.append(("fat_heavy", "Most of those calories came from fat; that's where the budget leaks."))
    if meal["carbs_g"] * 4 > 0.65 * max(meal["kcal"], 1) and meal["protein_g"] < 15:
        verdicts.append(("carb_heavy", "Carb-heavy with little protein, so expect to be hungry again soon."))

    moves = []
    if rem["kcal"] < 0:
        moves.append(f"You're {-rem['kcal']} kcal over today. Keep the rest of today to lean protein and veg, "
                     f"and I've trimmed the next couple of days slightly to even it out.")
    else:
        if rem["protein_g"] > 0:
            moves.append(f"{rem['kcal']} kcal and {rem['protein_g']} g protein left today. "
                         f"Make the next meal protein-first.")
        else:
            moves.append(f"Protein target hit. {rem['kcal']} kcal left for the day.")
    if "water_behind" in state["flags"]:
        moves.append("Drink a glass of water now; you're behind on hydration.")

    return {"verdicts": verdicts, "moves": moves}


def meal_feedback(user: User, meal_type: str, meal: dict[str, float], state: dict, description: str) -> str:
    youth = not state.get("show_calories", True)
    if youth:
        a = analyze_youth_meal(meal_type, meal, [description])
        numbers = f"(about {meal['protein_g']:.0f} g protein)"
    else:
        a = analyze_meal(user, meal_type, meal, state)
        numbers = f"({meal['kcal']:.0f} kcal, P{meal['protein_g']:.0f} C{meal['carbs_g']:.0f} F{meal['fat_g']:.0f})"
    fallback = " ".join([v[1] for v in a["verdicts"]] + a["moves"])
    llm = get_llm()
    if llm is None:
        return fallback
    try:
        return llm.text(
            system=system_prompt(user, state),
            messages=[{"role": "user", "content":
                       f"I just logged {meal_type}: {description} {numbers}.\n"
                       f"Your analysis notes: {json.dumps(a)}\n"
                       "Give me feedback on this meal and what to do next. 2-4 sentences."}],
            max_tokens=300,
        )
    except Exception:
        return fallback


# ---------- overage recovery ----------

def apply_recovery(session: Session, user: User, today: date, over_kcal: int) -> dict[str, Any]:
    """Spread a surplus over the next 2 days, capped at 10% of target per day, plus extra steps today.

    Idempotent: recomputes from the current overage each time a meal is logged/removed.
    Never applied to kids/teens: growing bodies don't get 'paid back' calories.
    """
    if user.age < 18:
        return {"over_kcal": 0, "trim_next_days_kcal": 0, "extra_steps_today": 0}
    cap = int(0.10 * user.target_kcal)
    per_day = min(max(over_kcal, 0) // 2, cap)
    per_day = int(round(per_day / 10) * 10)
    for i in (1, 2):
        log = get_daily_log(session, user, today + timedelta(days=i))
        log.kcal_adjustment = -per_day
        session.add(log)
    session.commit()
    extra_steps = min(int(max(over_kcal - 2 * per_day, 0) / KCAL_PER_STEP), 5000)
    extra_steps = int(round(extra_steps / 500) * 500)
    return {"over_kcal": over_kcal, "trim_next_days_kcal": per_day, "extra_steps_today": extra_steps}


# ---------- meal ideas ----------

def _home_match(user: User, allowed: set[str]) -> list[str]:
    hf = " ".join(user.home_foods).lower()
    out = []
    for name, (aliases, *_r) in FOODS.items():
        if name in allowed and any(t in hf for t in [name, *aliases]):
            out.append(name)
    return out


def _combo_stats(names: list[str], mults: list[float]) -> dict[str, float]:
    tot = {"kcal": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}
    for n, m in zip(names, mults):
        _a, _s, _g, kcal, p, c, f, _fib = FOODS[n]
        tot["kcal"] += kcal * m
        tot["protein_g"] += p * m
        tot["carbs_g"] += c * m
        tot["fat_g"] += f * m
    return {k: round(v) for k, v in tot.items()}


def candidate_meals(user: User, kcal_budget: int, protein_need: int, limit: int = 3) -> list[dict[str, Any]]:
    allowed = allowed_foods(user)
    home = set(_home_match(user, allowed))
    proteins = [p for p in PROTEIN_SOURCES if p in allowed]
    carbs = [c for c in CARB_SOURCES if c in allowed]
    vegs = [v for v in VEG_SOURCES if v in allowed]
    scored = []
    for p, c, v in itertools.product(proteins, carbs, vegs):
        for pm, cm in ((1, 1), (1.5, 1), (2, 1), (1, 2), (1.5, 2), (2, 2)):
            names, mults = [p, c, v], [pm, cm, 1]
            s = _combo_stats(names, mults)
            if s["kcal"] > kcal_budget * 1.05 or s["kcal"] < kcal_budget * 0.5:
                continue
            score = min(s["protein_g"], protein_need) * 2 - abs(kcal_budget - s["kcal"]) * 0.05
            score += 40 * len(home & set(names)) + (30 if p in home else 0)
            scored.append((score, names, mults, s))
    scored.sort(key=lambda x: -x[0])
    out, seen = [], set()
    for _score, names, mults, s in scored:
        if names[0] in seen:
            continue
        seen.add(names[0])
        desc = " + ".join(f"{fmt_qty(m, FOODS[n][1])} {n}" for n, m in zip(names, mults))
        short = protein_need - s["protein_g"]
        addon = None
        if short >= 10:
            addon = next((a for a in PROTEIN_ADDONS if a in allowed and not (a == "whey protein" and user.age < 18)), None)
            if addon:
                desc += f" (+ 1 {FOODS[addon][1].removeprefix('1 ')} {addon} to close the protein gap)"
                _a, _s, _g, k2, p2, c2, f2, _fb = FOODS[addon]
                s = {"kcal": s["kcal"] + k2, "protein_g": s["protein_g"] + round(p2), "carbs_g": s["carbs_g"] + round(c2),
                     "fat_g": s["fat_g"] + round(f2)}
        out.append({"title": f"{names[0].title()} plate", "items": desc, **s,
                    "from_home_foods": bool(home & set(names))})
        if len(out) >= limit:
            break
    return out


def meal_ideas(user: User, state: dict) -> dict[str, Any]:
    if not user.home_foods:
        return {
            "question": "Before I suggest meals: what do you usually cook or eat at home? "
                        "List a few staples (e.g. dal, roti, eggs, chicken curry, oats).",
            "ideas": [],
        }
    rem = state["remaining"]
    meals_left = max(1, 4 - len(state["meal_types_logged"]))
    budget = max(250, rem["kcal"] // meals_left if rem["kcal"] > 0 else 300)
    protein = max(20, rem["protein_g"] // meals_left if rem["protein_g"] > 0 else 25)
    ideas = candidate_meals(user, budget, protein)
    youth = not state.get("show_calories", True)
    intro = ("Build your next plate like this: something with protein, something with carbs for energy, "
             "and a fruit or veggie. Here are some ideas from foods you already eat:" if youth
             else f"Next meal target: ~{budget} kcal with ~{protein} g protein.")
    if youth:
        ideas = [{k: v for k, v in i.items() if k != "kcal"} for i in ideas]
    llm = get_llm()
    if llm is not None:
        try:
            intro = llm.text(
                system=system_prompt(user, state),
                messages=[{"role": "user", "content":
                           ("Suggest what I should eat next (no calorie talk). " if youth else
                            f"Suggest what I should eat next. Budget ~{budget} kcal, ~{protein} g protein. ") +
                           f"Candidate plates computed from my foods: {json.dumps(ideas)}. "
                           "Pick the best 2-3 (you may tweak using my home foods / cuisine), "
                           "say why in one line each, and add one meal-prep tip for the week."}],
                max_tokens=450,
            )
        except Exception:
            pass
    return {"question": None, "intro": intro, "ideas": ideas, "budget_kcal": budget, "protein_g": protein}
