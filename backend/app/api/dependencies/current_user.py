from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.finance import User

DatabaseSession = Annotated[Session, Depends(get_db)]


def get_current_user(db: DatabaseSession) -> User:
    settings = get_settings()
    if settings.app_env not in {"development", "test"}:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Production authentication is not configured",
        )
    user = db.scalar(select(User).where(User.email == settings.demo_user_email.lower()))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Development data is not seeded",
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]

