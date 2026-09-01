"""User service business logic layer."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.features.users.models import User
from app.features.users.repository import UserRepository
from app.features.users.schemas import UserUpdate


class UserService:
    @staticmethod
    def get_profile_by_uuid(
        db: Session, user_uuid: str, current_user: User
    ) -> User:
        """Fetch user profile by UUID with strict IDOR authorization check."""
        if str(current_user.user_uuid).strip() != str(user_uuid).strip():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to view this profile.",
            )

        user = UserRepository.get_by_uuid(db, user_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found.",
            )
        return user

    @staticmethod
    def update_profile(
        db: Session,
        user_uuid: str,
        user_update: UserUpdate,
        current_user: User,
    ) -> User:
        """Update user profile by UUID with strict IDOR authorization check."""
        if str(current_user.user_uuid).strip() != str(user_uuid).strip():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to modify this profile.",
            )

        user = UserRepository.get_by_uuid(db, user_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found.",
            )

        if user_update.full_name is not None:
            user.full_name = user_update.full_name
        if user_update.weight_kg is not None:
            user.weight_kg = user_update.weight_kg
        if user_update.gender is not None:
            user.gender = user_update.gender.value
        if user_update.activity_level is not None:
            user.activity_level = user_update.activity_level.value

        return UserRepository.update(db, user)
