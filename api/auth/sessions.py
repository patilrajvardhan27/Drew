import hashlib
import secrets
from datetime import timedelta

from fastapi import Depends, Request, Response
from sqlalchemy.orm import Session

from api.core.config import Settings
from api.core.db import get_session
from api.core.errors import AppError
from api.core.models import AuthSession, User, utcnow

COOKIE = "redraft_session"


def digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def start_session(session: Session, settings: Settings, user: User, response: Response) -> None:
    token = secrets.token_urlsafe(32)
    expires = utcnow() + timedelta(days=settings.session_days)
    session.add(AuthSession(token_hash=digest(token), user_id=user.id, expires_at=expires))
    session.commit()
    response.set_cookie(
        COOKIE,
        token,
        max_age=settings.session_days * 86400,
        httponly=True,
        samesite="lax",
        secure=settings.secure_cookies,
    )


def end_session(session: Session, request: Request, response: Response) -> None:
    token = request.cookies.get(COOKIE)
    if token:
        row = session.get(AuthSession, digest(token))
        if row:
            session.delete(row)
            session.commit()
    response.delete_cookie(COOKIE)


def optional_user(request: Request, session: Session = Depends(get_session)) -> User | None:
    token = request.cookies.get(COOKIE)
    if not token:
        return None
    row = session.get(AuthSession, digest(token))
    if row is None or row.expires_at < utcnow():
        return None
    return row.user


def required_user(user: User | None = Depends(optional_user)) -> User:
    if user is None:
        raise AppError(401, "Sign in to continue.")
    return user
