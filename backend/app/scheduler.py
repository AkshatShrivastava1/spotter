"""Background loop that runs the nudge engine for every user."""

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from sqlmodel import Session, select

from .coach.nudges import evaluate_user
from .config import get_settings
from .db import engine
from .models import User
from .push import send_push

log = logging.getLogger(__name__)


def run_nudges_once() -> int:
    sent = 0
    with Session(engine) as session:
        for user in session.exec(select(User)).all():
            try:
                for n in evaluate_user(session, user):
                    n.pushed = send_push(user, n)
                    session.add(n)
                    session.commit()
                    sent += 1
            except Exception:
                log.exception("nudge evaluation failed for user %s", user.id)
    return sent


def start_scheduler() -> BackgroundScheduler | None:
    s = get_settings()
    if not s.scheduler_enabled:
        return None
    sched = BackgroundScheduler()
    sched.add_job(run_nudges_once, "interval", minutes=s.nudge_interval_minutes, id="nudges")
    sched.start()
    return sched
