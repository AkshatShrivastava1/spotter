from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from sqlmodel import Session, select

from ..coach.chat import chat
from ..coach.checkin import CHECKIN_QUESTIONS, submit_checkin, weight_trend
from ..coach.context import day_state, get_daily_log, local_today, streak, week_summary
from ..coach.nudges import evaluate_user
from ..db import get_session
from ..deps import current_user
from ..models import CoachMessage, Notification, PhotoData, ProgressPhoto, User, WeeklyCheckin
from ..push import send_push
from ..schemas import AmountIn, ChatIn, CheckinIn

router = APIRouter(tags=["coach"])

PHOTO_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/heic", "image/heif"}
MAX_PHOTO_BYTES = 5 * 1024 * 1024


@router.get("/today")
def today(user: User = Depends(current_user), session: Session = Depends(get_session)):
    state = day_state(session, user)
    latest = session.exec(select(Notification).where(Notification.user_id == user.id)
                          .order_by(Notification.created_at.desc())).first()
    unread = len(session.exec(select(Notification.id).where(
        Notification.user_id == user.id, Notification.read == False)).all())  # noqa: E712
    return {**state, "streak": streak(session, user, local_today(user)),
            "coach_card": latest.model_dump() if latest else None, "unread": unread, "name": user.name}


# ---------- tracking ----------

@router.post("/track/water")
def add_water(body: AmountIn, user: User = Depends(current_user), session: Session = Depends(get_session)):
    log = get_daily_log(session, user, local_today(user))
    log.water_ml = max(0, log.water_ml + int(body.amount))
    session.add(log)
    session.commit()
    return {"water_ml": log.water_ml}


@router.post("/track/steps")
def set_steps(body: AmountIn, user: User = Depends(current_user), session: Session = Depends(get_session)):
    """Sets today's step total (phone pedometer reports cumulative)."""
    log = get_daily_log(session, user, local_today(user))
    log.steps = max(0, int(body.amount))
    session.add(log)
    session.commit()
    return {"steps": log.steps}


@router.post("/track/weight")
def set_weight(body: AmountIn, user: User = Depends(current_user), session: Session = Depends(get_session)):
    # Kids' weights can legitimately be under 30 kg; the app just never coaches on it.
    if not 10 < body.amount < 350:
        raise HTTPException(422, "weight looks off (kg)")
    today = local_today(user)
    log = get_daily_log(session, user, today)
    log.weight_kg = round(body.amount, 2)
    user.weight_kg = log.weight_kg
    session.add(log)
    session.add(user)
    session.commit()
    return weight_trend(session, user, today)


@router.get("/weight/trend")
def trend(user: User = Depends(current_user), session: Session = Depends(get_session)):
    return weight_trend(session, user, local_today(user))


# ---------- progress photos + weekly check-in ----------

@router.post("/progress-photos")
async def upload_progress_photo(file: UploadFile = File(...), pose: str = Form("front"),
                                user: User = Depends(current_user), session: Session = Depends(get_session)):
    if user.age < 18:
        raise HTTPException(403, "Progress photos are only available for adult accounts.")
    media_type = file.content_type or "image/jpeg"
    if media_type not in PHOTO_TYPES:
        raise HTTPException(415, "Photos must be JPEG, PNG, WebP or HEIC.")
    data = await file.read()
    if not data:
        raise HTTPException(422, "That photo is empty.")
    if len(data) > MAX_PHOTO_BYTES:
        raise HTTPException(413, "Photo is too large (max 5 MB).")
    # Stored in the database, not on disk: cloud hosts like Render wipe the disk on every deploy.
    p = ProgressPhoto(user_id=user.id, day=local_today(user), pose=pose, media_type=media_type)
    session.add(p)
    session.flush()
    session.add(PhotoData(photo_id=p.id, data=data))
    session.commit()
    session.refresh(p)
    return {"id": p.id, "day": p.day, "pose": p.pose}


@router.get("/progress-photos")
def list_photos(user: User = Depends(current_user), session: Session = Depends(get_session)):
    rows = session.exec(select(ProgressPhoto).where(ProgressPhoto.user_id == user.id)
                        .order_by(ProgressPhoto.day.desc())).all()
    return [{"id": p.id, "day": p.day, "pose": p.pose} for p in rows]


@router.get("/progress-photos/{photo_id}/image")
def photo_image(photo_id: int, user: User = Depends(current_user), session: Session = Depends(get_session)):
    p = session.get(ProgressPhoto, photo_id)
    if not p or p.user_id != user.id:
        raise HTTPException(404, "not found")
    blob = session.get(PhotoData, p.id)
    if blob:
        return Response(blob.data, media_type=p.media_type, headers={"Cache-Control": "private, max-age=86400"})
    if p.path and Path(p.path).is_file():  # saved to disk before photos moved into the database
        return FileResponse(p.path)
    raise HTTPException(404, "This photo is no longer available.")


@router.get("/checkin")
def checkin_status(user: User = Depends(current_user), session: Session = Depends(get_session)):
    today = local_today(user)
    last = session.exec(select(WeeklyCheckin).where(WeeklyCheckin.user_id == user.id)
                        .order_by(WeeklyCheckin.week_end.desc())).first()
    due = last is None or (today - last.week_end).days >= 6
    return {"due": due, "questions": CHECKIN_QUESTIONS, "last": last.model_dump() if last else None,
            "trend": weight_trend(session, user, today), "week": week_summary(session, user, today)}


@router.post("/checkin")
def checkin_submit(body: CheckinIn, user: User = Depends(current_user), session: Session = Depends(get_session)):
    return submit_checkin(session, user, local_today(user), body.answers, body.photo_ids)


@router.get("/checkin/history")
def checkin_history(user: User = Depends(current_user), session: Session = Depends(get_session)):
    return session.exec(select(WeeklyCheckin).where(WeeklyCheckin.user_id == user.id)
                        .order_by(WeeklyCheckin.week_end.desc())).all()


# ---------- chat + notifications ----------

@router.post("/coach/chat")
def coach_chat(body: ChatIn, user: User = Depends(current_user), session: Session = Depends(get_session)):
    return {"reply": chat(session, user, day_state(session, user), body.message)}


@router.get("/coach/messages")
def messages(user: User = Depends(current_user), session: Session = Depends(get_session)):
    rows = session.exec(select(CoachMessage).where(CoachMessage.user_id == user.id)
                        .order_by(CoachMessage.created_at.desc()).limit(100)).all()
    return rows[::-1]


@router.get("/notifications")
def notifications(user: User = Depends(current_user), session: Session = Depends(get_session)):
    return session.exec(select(Notification).where(Notification.user_id == user.id)
                        .order_by(Notification.created_at.desc()).limit(50)).all()


@router.post("/notifications/{nid}/read")
def mark_read(nid: int, user: User = Depends(current_user), session: Session = Depends(get_session)):
    n = session.get(Notification, nid)
    if not n or n.user_id != user.id:
        raise HTTPException(404, "not found")
    n.read = True
    session.add(n)
    session.commit()
    return {"ok": True}


@router.post("/notifications/run")
def run_now(user: User = Depends(current_user), session: Session = Depends(get_session)):
    """Dev helper: evaluate nudge rules for this user right now."""
    created = evaluate_user(session, user)
    for n in created:
        n.pushed = send_push(user, n)
        session.add(n)
    session.commit()
    return created


@router.get("/review/weekly")
def weekly(user: User = Depends(current_user), session: Session = Depends(get_session)):
    return week_summary(session, user, local_today(user))
