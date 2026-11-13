import secrets
from datetime import timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from api.auth import throttle
from api.auth.mailer import Mailer, get_mailer
from api.auth.passwords import hash_password
from api.auth.sessions import digest, start_session
from api.core.config import Settings, get_settings
from api.core.db import get_session
from api.core.errors import AppError
from api.core.models import AuthSession, PasswordReset, User, utcnow
from api.core.schemas import UserOut

router = APIRouter(prefix="/auth/password-reset", tags=["auth"])
LIFETIME = timedelta(hours=1)
SENT = "If an account uses that email, a reset link is on its way."


class ResetRequest(BaseModel):
    email: EmailStr


class ResetConfirm(BaseModel):
    token: str = Field(min_length=20, max_length=100)
    password: str = Field(min_length=10, max_length=200)


class Notice(BaseModel):
    detail: str


@router.post("", status_code=status.HTTP_202_ACCEPTED)
def request_reset(
    body: ResetRequest,
    request: Request,
    tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
    mailer: Mailer = Depends(get_mailer),
) -> Notice:
    """Answers the same way whether or not the account exists, so emails cannot be probed."""
    email = body.email.strip().lower()
    throttle.check(session, email, "reset")
    throttle.note(session, email, "reset")
    user = session.scalar(select(User).where(User.email == email))
    if user is not None:
        token = secrets.token_urlsafe(32)
        session.add(PasswordReset(token_hash=digest(token), user_id=user.id, expires_at=utcnow() + LIFETIME))
        session.commit()
        base = (settings.public_url or str(request.base_url)).rstrip("/")
        body_text = (
            f"Someone asked to reset the password for {email} on Redraft.\n\n"
            f"Choose a new password here within the hour:\n{base}/reset?token={token}\n\n"
            "If it was not you, ignore this email and nothing changes."
        )
        tasks.add_task(mailer.send, email, "Reset your Redraft password", body_text)
    return Notice(detail=SENT)


@router.post("/confirm")
def confirm_reset(
    body: ResetConfirm,
    response: Response,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> UserOut:
    reset = session.get(PasswordReset, digest(body.token))
    if reset is None or reset.expires_at < utcnow():
        raise AppError(400, "This reset link is invalid or has expired. Ask for a new one.")
    user = reset.user
    user.password_hash = hash_password(body.password)
    # A new password signs out every other device and spends every outstanding link.
    session.execute(delete(AuthSession).where(AuthSession.user_id == user.id))
    session.execute(delete(PasswordReset).where(PasswordReset.user_id == user.id))
    session.commit()
    throttle.clear(session, user.email, "login")
    start_session(session, settings, user, response)
    return UserOut.model_validate(user)
