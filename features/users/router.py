"""User endpoints router."""

from typing import Annotated
from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.features.users.models import User
from app.features.users.schemas import UserProfileResponse, UserUpdate
from app.features.users.service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/{user_uuid}",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user profile details by UUID",
)
def get_user_profile(
    user_uuid: Annotated[str, Path(description="The unique UUID of the user")],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    return UserService.get_profile_by_uuid(db, user_uuid, current_user)


@router.put(
    "/{user_uuid}",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user profile details by UUID",
)
def update_user_profile(
    user_uuid: Annotated[str, Path(description="The unique UUID of the user")],
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    return UserService.update_profile(
        db, user_uuid=user_uuid, user_update=user_update, current_user=current_user
    )
