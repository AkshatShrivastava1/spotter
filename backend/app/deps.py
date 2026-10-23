from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from .auth import user_id_from_token
from .db import get_session
from .models import User

_bearer = HTTPBearer(auto_error=False)


def current_user(creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
                 session: Session = Depends(get_session)) -> User:
    """Every app endpoint needs `Authorization: Bearer <token>` from /auth/signup or /auth/login."""
    uid = user_id_from_token(creds.credentials) if creds else None
    user = session.get(User, uid) if uid is not None else None
    if not user:
        raise HTTPException(401, "Please log in again.", headers={"WWW-Authenticate": "Bearer"})
    return user
