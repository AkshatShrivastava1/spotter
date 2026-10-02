"""Builds the factual snapshot the coach reasons over. No LLM here: pure numbers."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlmodel import Session, select

from ..models import DailyLog, Meal, User, WorkoutPlan, WorkoutSession
from ..targets import age_band


def local_now(user: User, now_utc: datetime | None = None) -> datetime:
    now_utc = now_utc or datetime.now(timezone.utc)
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=timezone.utc)
    return now_utc.astimezone(ZoneInfo(user.timezone))


def local_today(user: User, now_utc: datetime | None = None) -> date:
    return local_now(user, now_utc).date()


def _hm(s: str) -> float:
    h, m = s.split(":")
    return int(h) + int(m) / 60


def expected_fraction(user: User, now_local: datetime) -> float:
    """How much of the day's food 'should' be eaten by now (linear over the eating window)."""
    start = _hm(user.wake_time) + 0.5
    end = max(_hm(user.sleep_time) - 2.0, start + 6)
    hour = now_local.hour + now_local.minute / 60
    return max(0.0, min(1.0, (hour - start) / (end - start)))


def get_daily_log(session: Session, user: User, day: date) -> DailyLog:
    log = session.exec(
        select(DailyLog).where(DailyLog.user_id == user.id, DailyLog.day == day)
    ).first()
    if not log:
        log = DailyLog(user_id=user.id, day=day)
        session.add(log)
        session.commit()
        session.refresh(log)
    return log


def meals_for(session: Session, user: User, day: date) -> list[Meal]:
    return list(session.exec(
        select(Meal).where(Meal.user_id == user.id, Meal.day == day).order_by(Meal.logged_at)
    ))


def totals(meals: list[Meal]) -> dict[str, float]:
    return {
        "kcal": round(sum(m.kcal for m in meals)),
        "protein_g": round(sum(m.protein_g for m in meals)),
        "carbs_g": round(sum(m.carbs_g for m in meals)),
        "fat_g": round(sum(m.fat_g for m in meals)),
        "fiber_g": round(sum(m.fiber_g for m in meals)),
    }


def day_state(session: Session, user: User, day: date | None = None,
              now_utc: datetime | None = None) -> dict:
    now_l = local_now(user, now_utc)
    day = day or now_l.date()
    is_today = day == now_l.date()
    log = get_daily_log(session, user, day)
    meals = meals_for(session, user, day)
    eaten = totals(meals)

    target = {
        "kcal": user.target_kcal + log.kcal_adjustment,
        "protein_g": user.target_protein_g,
        "carbs_g": user.target_carbs_g,
        "fat_g": user.target_fat_g,
        "water_ml": user.target_water_ml,
        "steps": user.target_steps,
    }
    remaining = {k: round(target[k] - eaten[k]) for k in ("kcal", "protein_g", "carbs_g", "fat_g")}
    remaining["water_ml"] = target["water_ml"] - log.water_ml
    remaining["steps"] = target["steps"] - log.steps

    frac = expected_fraction(user, now_l) if is_today else 1.0
    workout_done = session.exec(
        select(WorkoutSession).where(WorkoutSession.user_id == user.id, WorkoutSession.day == day)
    ).first() is not None

    plan = session.exec(
        select(WorkoutPlan).where(WorkoutPlan.user_id == user.id, WorkoutPlan.active == True)  # noqa: E712
    ).first()
    todays_plan_day = None
    if plan:
        dow = day.strftime("%a")
        todays_plan_day = next((d for d in plan.days if d.get("day") == dow), None)

    band = age_band(user.age)
    youth = band in ("child", "teen")
    flags = []
    if eaten["kcal"] > target["kcal"] and not youth:
        flags.append("over_kcal")
    if is_today and frac >= 0.5 and eaten["protein_g"] < target["protein_g"] * frac * 0.75:
        flags.append("protein_behind")
    if is_today and frac >= 0.4 and log.water_ml < target["water_ml"] * frac * 0.6:
        flags.append("water_behind")
    if is_today and frac >= 0.6 and log.steps < target["steps"] * frac * 0.6:
        flags.append("steps_behind")
    if todays_plan_day and not workout_done:
        flags.append("workout_pending")

    return {
        "age_band": band,
        # Kids/teens never see calorie budgets; the app shows habits (protein, plants, water, movement) instead.
        "show_calories": not youth,
        "day": day.isoformat(),
        "local_time": now_l.strftime("%H:%M"),
        "expected_fraction": round(frac, 2),
        "target": target,
        "eaten": eaten,
        "remaining": remaining,
        "water_ml": log.water_ml,
        "steps": log.steps,
        "weight_kg": log.weight_kg,
        "kcal_adjustment": log.kcal_adjustment,
        "meals": [
            {"id": m.id, "meal_type": m.meal_type, "description": m.description,
             "kcal": round(m.kcal), "protein_g": round(m.protein_g), "carbs_g": round(m.carbs_g),
             "fat_g": round(m.fat_g), "source": m.source, "coach_feedback": m.coach_feedback,
             "items": m.items}
            for m in meals
        ],
        "meal_types_logged": sorted({m.meal_type for m in meals}),
        "workout_done": workout_done,
        "todays_workout": todays_plan_day,
        "flags": flags,
    }


def streak(session: Session, user: User, today: date) -> int:
    """Consecutive days with at least 2 meals logged, counting back from today (or yesterday)."""
    count = 0
    d = today
    # Today counts only if already logged; otherwise start from yesterday so the streak isn't 'lost' at 8am.
    if len(meals_for(session, user, d)) < 2:
        d -= timedelta(days=1)
    while len(meals_for(session, user, d)) >= 2:
        count += 1
        d -= timedelta(days=1)
        if count > 365:
            break
    return count


def week_summary(session: Session, user: User, end: date) -> dict:
    days = [end - timedelta(days=i) for i in range(6, -1, -1)]
    rows = []
    for d in days:
        ms = meals_for(session, user, d)
        log = session.exec(select(DailyLog).where(DailyLog.user_id == user.id, DailyLog.day == d)).first()
        t = totals(ms)
        adj = log.kcal_adjustment if log else 0
        rows.append({
            "day": d.isoformat(), "logged": len(ms) > 0, **t,
            "target_kcal": user.target_kcal + adj,
            "water_ml": log.water_ml if log else 0, "steps": log.steps if log else 0,
            "weight_kg": log.weight_kg if log else None,
            "workout": session.exec(select(WorkoutSession).where(
                WorkoutSession.user_id == user.id, WorkoutSession.day == d)).first() is not None,
        })
    logged = [r for r in rows if r["logged"]]
    n = len(logged) or 1
    weights = [r["weight_kg"] for r in rows if r["weight_kg"]]
    return {
        "days": rows,
        "days_logged": len(logged),
        "avg_kcal": round(sum(r["kcal"] for r in logged) / n),
        "avg_protein_g": round(sum(r["protein_g"] for r in logged) / n),
        "days_on_target": sum(1 for r in logged if abs(r["kcal"] - r["target_kcal"]) <= 0.1 * r["target_kcal"]),
        "days_protein_hit": sum(1 for r in logged if r["protein_g"] >= 0.9 * user.target_protein_g),
        "workouts": sum(1 for r in rows if r["workout"]),
        "avg_steps": round(sum(r["steps"] for r in rows) / 7),
        "weight_change_kg": round(weights[-1] - weights[0], 1) if len(weights) >= 2 else None,
    }
