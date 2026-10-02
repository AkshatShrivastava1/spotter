from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..coach.context import local_today
from ..coach.training import create_plan, progression, session_feedback
from ..data.exercises import EXERCISES
from ..db import get_session
from ..deps import current_user
from ..models import User, WorkoutPlan, WorkoutSession
from ..schemas import WorkoutSessionIn

router = APIRouter(tags=["training"])


@router.get("/exercises")
def exercises():
    return [{"slug": k, **v} for k, v in EXERCISES.items()]


@router.get("/exercises/{slug}")
def exercise(slug: str):
    if slug not in EXERCISES:
        raise HTTPException(404, "unknown exercise")
    return {"slug": slug, **EXERCISES[slug]}


@router.get("/workouts/plan")
def plan(user: User = Depends(current_user), session: Session = Depends(get_session)):
    p = session.exec(select(WorkoutPlan).where(WorkoutPlan.user_id == user.id,
                                               WorkoutPlan.active == True)).first()  # noqa: E712
    return p or create_plan(session, user)


@router.post("/workouts/plan/generate")
def regenerate(user: User = Depends(current_user), session: Session = Depends(get_session)):
    return create_plan(session, user)


@router.post("/workouts/sessions")
def log_session(body: WorkoutSessionIn, user: User = Depends(current_user), session: Session = Depends(get_session)):
    exs = [e.model_dump() for e in body.exercises]
    prog = progression(session, user, exs)  # compare before saving so PRs are vs history
    ws = WorkoutSession(user_id=user.id, day=local_today(user), focus=body.focus, exercises=exs,
                        duration_min=body.duration_min)
    ws.coach_feedback = session_feedback(user, body.focus, prog)
    session.add(ws)
    session.commit()
    session.refresh(ws)
    return {"session": ws.model_dump(), "progression": prog, "feedback": ws.coach_feedback}


@router.get("/workouts/sessions")
def sessions(user: User = Depends(current_user), session: Session = Depends(get_session)):
    return session.exec(select(WorkoutSession).where(WorkoutSession.user_id == user.id)
                        .order_by(WorkoutSession.logged_at.desc()).limit(30)).all()


@router.get("/workouts/last/{slug}")
def last_for(slug: str, user: User = Depends(current_user), session: Session = Depends(get_session)):
    """Most recent sets for an exercise, so the app can prefill 'last time: 60 kg x 8'."""
    for ws in session.exec(select(WorkoutSession).where(WorkoutSession.user_id == user.id)
                           .order_by(WorkoutSession.logged_at.desc())):
        for e in ws.exercises:
            if e.get("slug") == slug:
                return {"day": ws.day, "sets": e.get("sets", [])}
    return {"day": None, "sets": []}
