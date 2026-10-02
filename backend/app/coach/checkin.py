"""Weight trend + the weekly check-in (the 'sit down with your trainer' moment)."""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any

from sqlmodel import Session, select

from ..llm import get_llm
from ..models import DailyLog, ProgressPhoto, User, WeeklyCheckin
from .context import week_summary
from .persona import system_prompt


def weekly_weight_averages(session: Session, user: User, end: date, weeks: int = 8) -> list[dict[str, Any]]:
    """Rolling 7-day blocks ending on `end`. Daily weight bounces 1-2 kg on water; averages don't."""
    out = []
    for w in range(weeks - 1, -1, -1):
        block_end = end - timedelta(days=7 * w)
        block_start = block_end - timedelta(days=6)
        rows = session.exec(select(DailyLog).where(
            DailyLog.user_id == user.id, DailyLog.day >= block_start, DailyLog.day <= block_end,
            DailyLog.weight_kg != None)).all()  # noqa: E711
        ws = [r.weight_kg for r in rows if r.weight_kg]
        out.append({"week_start": block_start.isoformat(), "week_end": block_end.isoformat(),
                    "avg_kg": round(sum(ws) / len(ws), 2) if ws else None, "weigh_ins": len(ws)})
    return out


def weight_trend(session: Session, user: User, end: date) -> dict[str, Any]:
    weeks = weekly_weight_averages(session, user, end)
    daily = session.exec(select(DailyLog).where(
        DailyLog.user_id == user.id, DailyLog.day > end - timedelta(days=60), DailyLog.weight_kg != None  # noqa: E711
    ).order_by(DailyLog.day)).all()
    cur, prev = weeks[-1]["avg_kg"], weeks[-2]["avg_kg"]
    change = round(cur - prev, 2) if cur is not None and prev is not None else None
    pct = round(100 * change / prev, 2) if change is not None and prev else None
    return {
        "daily": [{"day": d.day.isoformat(), "kg": d.weight_kg} for d in daily],
        "weekly": weeks,
        "this_week_avg": cur, "last_week_avg": prev,
        "change_kg": change, "change_pct": pct,
        "verdict": _rate_verdict(user.goal, pct),
    }


def _rate_verdict(goal: str, pct: float | None) -> str:
    if pct is None:
        return "Need at least 2 weigh-ins in each of the last two weeks to compare averages."
    if goal == "lose":
        if pct <= -1.0:
            return "Dropping fast (>1%/week). Risk of muscle loss; consider eating a bit more."
        if pct <= -0.4:
            return "Right on pace (0.4-1% per week). Keep doing exactly this."
        if pct < 0:
            return "Moving, but slowly."
        return "Not dropping. Either intake is higher than logged, or the target needs a trim."
    if goal == "gain":
        if pct >= 0.6:
            return "Gaining fast; some of that is likely fat. Ease off slightly."
        if pct >= 0.2:
            return "Good lean-gain pace."
        return "Not gaining yet. Eat a bit more."
    return "Stable." if abs(pct) < 0.5 else "Drifting from maintenance."


def recommend_adjustment(user: User, trend: dict[str, Any], summary: dict[str, Any]) -> int:
    """Only adjust when adherence is good; otherwise the fix is consistency, not new numbers."""
    pct = trend["change_pct"]
    if pct is None or summary["days_logged"] < 5:
        return 0
    if user.goal == "lose":
        if pct > -0.2:
            return -150
        if pct < -1.0:
            return 150
    elif user.goal == "gain":
        if pct < 0.1:
            return 150
        if pct > 0.6:
            return -100
    else:
        if pct > 0.5:
            return -100
        if pct < -0.5:
            return 100
    return 0


CHECKIN_QUESTIONS = [
    {"key": "energy", "q": "Energy this week (1-5)?", "type": "scale"},
    {"key": "hunger", "q": "Hunger this week (1 = never hungry, 5 = starving)?", "type": "scale"},
    {"key": "sleep", "q": "Sleep quality (1-5)?", "type": "scale"},
    {"key": "stress", "q": "Stress (1-5)?", "type": "scale"},
    {"key": "wins", "q": "One win this week?", "type": "text"},
    {"key": "struggles", "q": "What got in the way?", "type": "text"},
]


def submit_checkin(session: Session, user: User, today: date, answers: dict[str, Any],
                   photo_ids: list[int]) -> WeeklyCheckin:
    trend = weight_trend(session, user, today)
    summary = week_summary(session, user, today)
    youth = user.age < 18
    adj = 0 if youth else recommend_adjustment(user, trend, summary)
    if user.goal == "lose" and answers.get("hunger", 0) >= 5 and adj < 0:
        adj = 0  # starving + stalled: fix food quality first, not fewer calories
    if adj:
        floor = 1500 if user.sex == "male" else 1200
        user.target_kcal = max(floor, user.target_kcal + adj)
        user.target_carbs_g = max(50, user.target_carbs_g + round(adj / 4))
        session.add(user)

    photos = session.exec(select(ProgressPhoto).where(ProgressPhoto.user_id == user.id)).all()
    facts = {
        "display_units": "lb" if user.units == "imperial" else "kg (weights in facts are kg; convert if lb)",
        "weight": {k: trend[k] for k in ("this_week_avg", "last_week_avg", "change_kg", "change_pct", "verdict")},
        "week": {k: v for k, v in summary.items() if k != "days"},
        "answers": answers,
        "kcal_target_change": adj,
        "new_kcal_target": user.target_kcal,
        "progress_photos_total": len(photos),
        "photos_this_week": len(photo_ids),
    }
    if youth:
        facts.pop("weight")
        facts["week"].pop("avg_kcal", None)
        facts["week"].pop("days_on_target", None)
        facts["week"].pop("weight_change_kg", None)
        facts.pop("new_kcal_target")
        facts.pop("progress_photos_total")
        facts.pop("photos_this_week")
    review = _youth_review(facts) if youth else _fallback_review(user, facts)
    llm = get_llm()
    if llm is not None:
        try:
            review = llm.text(
                system=system_prompt(user),
                messages=[{"role": "user", "content":
                           "Run my weekly check-in like a personal trainer would on a call. Facts: "
                           + json.dumps(facts) +
                           ("\nStructure: 1) celebrate what went well, 2) ONE fun habit goal for next week "
                            "(movement, water, fruit/veg, sleep). No weight or calorie talk. Under 120 words."
                            if youth else
                            "\nStructure: 1) how the scale trend actually looks (averages, not single days), "
                            "2) what went well, 3) the ONE thing to fix this week with a specific plan, "
                            "4) any target change and why. Under 180 words.")}],
                max_tokens=600,
            )
        except Exception:
            pass

    ci = WeeklyCheckin(
        user_id=user.id, week_end=today, avg_weight_kg=trend["this_week_avg"],
        prev_avg_weight_kg=trend["last_week_avg"], stats=facts, answers=answers,
        photo_ids=photo_ids, coach_review=review, kcal_change=adj,
    )
    session.add(ci)
    session.commit()
    session.refresh(ci)
    return ci


def _fallback_review(user: User, f: dict[str, Any]) -> str:
    w, wk = f["weight"], f["week"]
    parts = []
    if w["this_week_avg"] is not None and w["last_week_avg"] is not None:
        k, u = (2.20462, "lb") if user.units == "imperial" else (1.0, "kg")
        parts.append(f"Weekly average {w['last_week_avg'] * k:.1f} -> {w['this_week_avg'] * k:.1f} {u} "
                     f"({w['change_kg'] * k:+.1f} {u}). {w['verdict']}")
    else:
        parts.append(w["verdict"])
    parts.append(f"You logged {wk['days_logged']}/7 days, hit protein on {wk['days_protein_hit']}, "
                 f"trained {wk['workouts']}x, averaged {wk['avg_steps']:,} steps.")
    if wk["days_logged"] < 5:
        parts.append("Focus this week: log every day, even the messy ones. I can't adjust what I can't see.")
    elif wk["days_protein_hit"] < 4:
        parts.append("Focus this week: protein. Put a protein source on the plate first at every meal.")
    else:
        parts.append("Focus this week: keep the same habits and add 1,000 steps a day.")
    if f["kcal_target_change"]:
        parts.append(f"I'm changing your target by {f['kcal_target_change']:+} kcal to {f['new_kcal_target']}.")
    if not f["photos_this_week"]:
        parts.append("No progress photos this week. Take them next Sunday: the scale lies more than the mirror.")
    return " ".join(parts)


def _youth_review(f: dict[str, Any]) -> str:
    wk = f["week"]
    parts = [f"This week you logged {wk['days_logged']} days, did {wk['workouts']} workouts and averaged "
             f"{wk['avg_steps']:,} steps."]
    if f["answers"].get("wins"):
        parts.append(f"Your win: {f['answers']['wins']}. That's awesome.")
    if wk["avg_steps"] < 10000:
        parts.append("Next week's mission: get outside and play or walk for an hour every day.")
    elif wk["days_protein_hit"] < 4:
        parts.append("Next week's mission: have eggs, dal, yogurt, paneer or chicken with every meal.")
    else:
        parts.append("Next week's mission: try one new fruit or vegetable.")
    return " ".join(parts)
