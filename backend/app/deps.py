from fastapi import Depends, Header, HTTPException
from sqlmodel import Session

from .db import get_session
from .models import User


def current_user(x_user_id: int = Header(...), session: Session = Depends(get_session)) -> User:
    """MVP auth: the app stores the id returned at onboarding. Replace with real auth (Supabase/Clerk) later."""
    user = session.get(User, x_user_id)
    if not user:
        raise HTTPException(404, "user not found")
    return user
