from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlmodel import Session, select

from ..coach.context import day_state, local_today
from ..coach.feedback import apply_recovery, meal_feedback, meal_ideas
from ..coach.nudges import notify
from ..coach.nutrition import parse_photo, parse_text, sum_items
from ..db import get_session
from ..deps import current_user
from ..models import Meal, Notification, User
from ..push import send_push
from ..schemas import MealIn, ParseIn

router = APIRouter(tags=["nutrition"])

MAX_PHOTO_BYTES = 8 * 1024 * 1024


@router.post("/food/parse")
def parse(body: ParseIn, user: User = Depends(current_user)):
    out = parse_text(body.text)
    return {**out, "totals": sum_items(out["items"])}


@router.post("/food/photo")
async def photo(file: UploadFile = File(...), note: str = Form(""), user: User = Depends(current_user)):
    data = await file.read()
    if len(data) > MAX_PHOTO_BYTES:
        raise HTTPException(413, "photo too large (max 8 MB)")
    media = file.content_type or "image/jpeg"
    if media not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
        raise HTTPException(415, "use a jpeg, png or webp image")
    out = parse_photo(data, media, note)
    return {**out, "totals": sum_items(out["items"])}


def _recovery_check(session: Session, user: User) -> dict | None:
    if user.age < 18:
        return None  # kids/teens never get 'over budget' messaging or paid-back calories
    today = local_today(user)
    state = day_state(session, user, today)
    over = -state["remaining"]["kcal"]
    plan = apply_recovery(session, user, today, over)
    if over <= 0:
        return None
    already = session.exec(select(Notification).where(
        Notification.user_id == user.id, Notification.day == today, Notification.kind == "over_budget")).first()
    if not already:
        body = (f"You're {over} kcal over today. No crash dieting: I've trimmed the next 2 days by "
                f"{plan['trim_next_days_kcal']} kcal each"
                + (f" and a {plan['extra_steps_today']:,}-step walk today closes the rest." if plan["extra_steps_today"] else ".")
                )
        n = notify(session, user, today, "over_budget", "Over budget: here's the fix", body)
        n.pushed = send_push(user, n)
        session.add(n)
        session.commit()
    return plan


@router.post("/meals")
def log_meal(body: MealIn, user: User = Depends(current_user), session: Session = Depends(get_session)):
    if not body.items:
        raise HTTPException(422, "add at least one item")
    items = [i.model_dump() for i in body.items]
    tot = sum_items(items)
    desc = body.description or ", ".join(f"{i['quantity']} {i['name']}".strip() for i in items)
    meal = Meal(user_id=user.id, day=local_today(user), meal_type=body.meal_type, source=body.source,
                description=desc, items=items, kcal=tot["kcal"], protein_g=tot["protein_g"],
                carbs_g=tot["carbs_g"], fat_g=tot["fat_g"], fiber_g=tot["fiber_g"])
    session.add(meal)
    session.commit()
    session.refresh(meal)

    recovery = _recovery_check(session, user)
    state = day_state(session, user)
    meal.coach_feedback = meal_feedback(user, body.meal_type, tot, state, desc)
    session.add(meal)
    session.commit()
    session.refresh(meal)
    return {"meal": meal.model_dump(), "feedback": meal.coach_feedback, "recovery": recovery, "today": state}


@router.delete("/meals/{meal_id}")
def delete_meal(meal_id: int, user: User = Depends(current_user), session: Session = Depends(get_session)):
    meal = session.get(Meal, meal_id)
    if not meal or meal.user_id != user.id:
        raise HTTPException(404, "meal not found")
    session.delete(meal)
    session.commit()
    _recovery_check(session, user)
    return {"ok": True}


@router.get("/meal-ideas")
def ideas(user: User = Depends(current_user), session: Session = Depends(get_session)):
    return meal_ideas(user, day_state(session, user))
