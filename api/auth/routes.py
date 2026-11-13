from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.auth import throttle
from api.auth.passwords import hash_password, verify_password
from api.auth.sessions import end_session, required_user, start_session
from api.core.config import Settings, get_settings
from api.core.db import get_session
from api.core.errors import AppError
from api.core.models import User
from api.core.schemas import Credentials, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _normalise(email: str) -> str:
    return email.strip().lower()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    body: Credentials,
    response: Response,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> UserOut:
    email = _normalise(body.email)
    if session.scalar(select(func.count()).select_from(User).where(User.email == email)):
        raise AppError(409, "An account with this email already exists.")
    user = User(email=email, password_hash=hash_password(body.password))
    session.add(user)
    session.commit()
    start_session(session, settings, user, response)
    return UserOut.model_validate(user)


@router.post("/login")
def login(
    body: Credentials,
    response: Response,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> UserOut:
    email = _normalise(body.email)
    throttle.check(session, email, "login")
    user = session.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(body.password, user.password_hash):
        throttle.note(session, email, "login")
        raise AppError(401, "Email or password is incorrect.")
    throttle.clear(session, email, "login")
    start_session(session, settings, user, response)
    return UserOut.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, session: Session = Depends(get_session)) -> Response:
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    end_session(session, request, response)
    return response


@router.get("/me")
def me(user: User = Depends(required_user)) -> UserOut:
    return UserOut.model_validate(user)
