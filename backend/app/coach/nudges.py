"""Proactive coaching engine: the part that makes Spotter 'on you' instead of waiting to be opened.

Runs every N minutes for every user. Each rule fires at most once per local day
(keyed by `kind`), only inside its time window, and only if its condition holds.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlmodel import Session, select

from ..llm import get_llm
from ..models import Meal, Notification, User, WeeklyCheckin
from .context import _hm, day_state, local_now
from .persona import system_prompt


@dataclass
class Rule:
    kind: str
    start: Callable[[User], float]  # local hour (float) window start
    end: Callable[[User], float]
    when: Callable[[dict, User, Session, date], bool]
    title: str
    body: Callable[[dict, User], str]
    weekday: int | None = None  # 0=Mon .. 6=Sun
    adults_only: bool = False  # weight/calorie-centric nudges never go to kids or teens


def _y(s: dict) -> bool:
    """True when the user is a kid/teen (no calorie talk)."""
    return not s.get("show_calories", True)


def _wake(u: User) -> float:
    return _hm(u.wake_time)


def _sleep(u: User) -> float:
    return _hm(u.sleep_time) if _hm(u.sleep_time) > 12 else 23.5


def _no_meals_two_days(s: dict, u: User, sess: Session, day: date) -> bool:
    since = day - timedelta(days=2)
    return sess.exec(select(Meal).where(Meal.user_id == u.id, Meal.day >= since)).first() is None


def _no_checkin_this_week(s: dict, u: User, sess: Session, day: date) -> bool:
    return sess.exec(select(WeeklyCheckin).where(
        WeeklyCheckin.user_id == u.id, WeeklyCheckin.week_end > day - timedelta(days=6))).first() is None


RULES: list[Rule] = [
    Rule("weigh_in", lambda u: _wake(u), lambda u: _wake(u) + 3,
         lambda s, u, sess, d: s["weight_kg"] is None,
         "Morning weigh-in",
         lambda s, u: "Step on the scale before you eat or drink, after the bathroom. "
                      "One number a day; I compare weekly averages, so don't stress the daily bounce.",
         adults_only=True),
    Rule("morning_brief", lambda u: _wake(u) + 0.5, lambda u: 11.5,
         lambda s, u, sess, d: True,
         "Today's game plan",
         lambda s, u: ("Today's mission: a good breakfast with protein, fruit or veg at lunch, "
                       f"{s['target']['water_ml'] / 1000:.1f} L of water, and at least 60 minutes of moving or playing."
                       + (f" Workout: {s['todays_workout']['focus']}." if s['todays_workout'] else "")) if _y(s) else
                      (f"Today: {s['target']['kcal']} kcal, {s['target']['protein_g']} g protein, "
                       f"{s['target']['water_ml'] / 1000:.1f} L water, {s['target']['steps']:,} steps."
                       + (f" Workout: {s['todays_workout']['focus']}." if s['todays_workout'] else " Rest day: walk.")
                       + (f" (Trimmed {-s['kcal_adjustment']} kcal to balance yesterday.)"
                          if s['kcal_adjustment'] < 0 else ""))),
    Rule("lunch_missing", lambda u: 14.0, lambda u: 16.0,
         lambda s, u, sess, d: "lunch" not in s["meal_types_logged"] and len(s["meals"]) < 2,
         "Did you eat lunch?",
         lambda s, u: "No lunch logged yet. If you ate, log it now while you remember. "
                      "If you didn't, eat something with protein before you get ravenous tonight."),
    Rule("water_pace", lambda u: 13.0, lambda u: 19.0,
         lambda s, u, sess, d: "water_behind" in s["flags"],
         "Water check",
         lambda s, u: f"You're at {s['water_ml']} ml of {s['target']['water_ml']} ml. Two glasses in the next hour."),
    Rule("protein_pace", lambda u: 16.0, lambda u: 20.0,
         lambda s, u, sess, d: "protein_behind" in s["flags"],
         "Protein is behind",
         lambda s, u: f"{s['eaten']['protein_g']} g of {s['target']['protein_g']} g protein so far. "
                      f"Dinner needs about {max(s['remaining']['protein_g'], 0)} g; build it around the protein first."),
    Rule("workout_pending", lambda u: 17.0, lambda u: 20.0,
         lambda s, u, sess, d: "workout_pending" in s["flags"],
         "Workout's still on the board",
         lambda s, u: f"{s['todays_workout']['focus'] if s['todays_workout'] else 'Training'} day and it's not logged. "
                      "Even 30 minutes of the main lifts counts. Go."),
    Rule("steps_pace", lambda u: 17.5, lambda u: 20.5,
         lambda s, u, sess, d: "steps_behind" in s["flags"],
         "Get your steps",
         lambda s, u: f"{s['steps']:,} / {s['target']['steps']:,} steps. A 20-minute walk after dinner closes most of that gap."),
    Rule("dinner_missing", lambda u: 21.0, lambda u: _sleep(u) - 0.5,
         lambda s, u, sess, d: "dinner" not in s["meal_types_logged"] and len(s["meals"]) >= 1,
         "Dinner logged?",
         lambda s, u: "Did you have dinner? Add it so your day is complete." if _y(s) else
                      f"No dinner yet. You have {max(s['remaining']['kcal'], 0)} kcal left. Log it so tomorrow's plan is right."),
    Rule("evening_checkin", lambda u: _sleep(u) - 1.5, lambda u: _sleep(u),
         lambda s, u, sess, d: len(s["meals"]) > 0,
         "End-of-day check-in",
         lambda s, u: ("How did today go? Did you drink your water, eat a fruit or veggie, and get moving? "
                       "Tell me one thing you did well.") if _y(s) else
                      (f"Today: {s['eaten']['kcal']} / {s['target']['kcal']} kcal, "
                       f"{s['eaten']['protein_g']} / {s['target']['protein_g']} g protein. "
                       "Anything you ate that isn't logged? Be honest; I can only coach what I can see.")),
    Rule("ghosting", lambda u: 12.0, lambda u: 19.0, _no_meals_two_days,
         "Haven't heard from you",
         lambda s, u: "Two days, no logs. No judgment, just tell me what you ate today (rough is fine) and we reset."),
    Rule("weekly_checkin", lambda u: 10.0, lambda u: 20.0, _no_checkin_this_week,
         "Weekly check-in time",
         lambda s, u: ("Let's look back at your week: how much you moved, how you slept, and one thing to try next week."
                       if _y(s) else
                       "Let's review your week: I'll pull your weight average vs last week. "
                       "Take front + side progress photos (same light, same spot) and answer 4 quick questions."),
         weekday=6),
]


def _voice(user: User, state: dict, title: str, body: str) -> str:
    llm = get_llm()
    if llm is None:
        return body
    try:
        return llm.text(
            system=system_prompt(user, state),
            messages=[{"role": "user", "content":
                       f"Write a push notification for '{title}'. Facts to convey: {body}\n"
                       "Max 2 sentences, in your voice, no emojis, no greeting."}],
            max_tokens=120,
        )
    except Exception:
        return body


def notify(session: Session, user: User, day: date, kind: str, title: str, body: str) -> Notification:
    n = Notification(user_id=user.id, day=day, kind=kind, title=title, body=body)
    session.add(n)
    session.commit()
    session.refresh(n)
    return n


def evaluate_user(session: Session, user: User, now_utc: datetime | None = None,
                  use_llm: bool = True) -> list[Notification]:
    now_l = local_now(user, now_utc)
    day = now_l.date()
    hour = now_l.hour + now_l.minute / 60
    state = day_state(session, user, day, now_utc)
    sent_today = set(session.exec(
        select(Notification.kind).where(Notification.user_id == user.id, Notification.day == day)))
    created = []
    for r in RULES:
        if r.kind in sent_today:
            continue
        if r.adults_only and _y(state):
            continue
        if r.weekday is not None and now_l.weekday() != r.weekday:
            continue
        if not (r.start(user) <= hour < r.end(user)):
            continue
        if not r.when(state, user, session, day):
            continue
        body = r.body(state, user)
        if use_llm:
            body = _voice(user, state, r.title, body)
        created.append(notify(session, user, day, r.kind, r.title, body))
        # One nudge per tick: don't spam three notifications at once.
        break
    return created


def debug_rules() -> str:
    return json.dumps([r.kind for r in RULES])
