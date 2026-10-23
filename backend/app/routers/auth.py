from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..auth import clear_failures, create_token, hash_password, record_failure, too_many_attempts, verify_password
from ..coach.training import create_plan
from ..db import get_session
from ..models import User
from ..schemas import LoginIn, SignupIn
from .users import apply_targets, public_user

router = APIRouter(prefix="/auth", tags=["auth"])


def _norm(email: str) -> str:
    return email.strip().lower()


@router.post("/signup")
def signup(body: SignupIn, session: Session = Depends(get_session)):
    """Create an account and finish onboarding in one step."""
    email = _norm(body.email)
    if session.exec(select(User).where(User.email == email)).first():
        raise HTTPException(409, "An account with that email already exists. Try logging in.")
    data = body.model_dump(exclude={"email", "password"})
    user = User(**data, email=email, password_hash=hash_password(body.password))
    energy = apply_targets(user)
    session.add(user)
    session.commit()
    session.refresh(user)
    plan = create_plan(session, user)
    session.refresh(user)
    return {"access_token": create_token(user.id), "user": public_user(user), "energy": energy, "plan_id": plan.id}


@router.post("/login")
def login(body: LoginIn, session: Session = Depends(get_session)):
    email = _norm(body.email)
    if too_many_attempts(email):
        raise HTTPException(429, "Too many attempts. Wait 15 minutes and try again.")
    user = session.exec(select(User).where(User.email == email)).first()
    if not user or not verify_password(body.password, user.password_hash):
        record_failure(email)
        raise HTTPException(401, "Wrong email or password.")
    clear_failures(email)
    return {"access_token": create_token(user.id), "user": public_user(user)}
