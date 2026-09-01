"""FastAPI shared dependencies."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.features.users.models import User
from app.features.users.repository import UserRepository

# HTTPBearer scheme so Swagger UI prompts for raw Bearer token string
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Validate Bearer JWT and retrieve current authenticated user."""
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_uuid: str | None = payload.get("sub")
        if user_uuid is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = UserRepository.get_by_uuid(db, user_uuid)
    if user is None:
        raise credentials_exception
    return user
