"""Authentication business logic service."""

import uuid
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.features.auth.schemas import LoginResponse, UserLogin
from app.features.goals.models import Settings
from app.features.goals.service import GoalService
from app.features.reminders.models import ReminderSettings
from app.features.users.models import User
from app.features.users.repository import UserRepository
from app.features.users.schemas import UserCreate


class AuthService:
    @staticmethod
    def register_user(db: Session, user_in: UserCreate) -> User:
        """Register new user, initialize settings and reminders in a single transaction."""
        normalized_email = user_in.email.strip().lower()
        existing = UserRepository.get_by_email(db, normalized_email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already registered.",
            )

        try:
            gender_val = (
                user_in.gender.value if user_in.gender else "other"
            )
            activity_val = (
                user_in.activity_level.value
                if user_in.activity_level
                else "moderate"
            )

            new_user = User(
                user_uuid=str(uuid.uuid4()),
                email=normalized_email,
                hashed_password=hash_password(user_in.password),
                full_name=user_in.full_name,
                weight_kg=user_in.weight_kg,
                gender=gender_val,
                activity_level=activity_val,
            )
            UserRepository.create(db, new_user)
            db.flush()

            # Calculate personalized daily goal or use custom goal
            if user_in.daily_goal_ml:
                computed_goal = user_in.daily_goal_ml
            else:
                rec = GoalService.compute_water_recommendation(
                    weight_kg=user_in.weight_kg or 70.0,
                    gender=gender_val,
                    activity_level=activity_val,
                )
                computed_goal = rec["recommended_daily_ml"]

            db.add(Settings(daily_goal_ml=computed_goal, user_id=new_user.id))
            db.add(ReminderSettings(user_id=new_user.id))
            db.commit()
            db.refresh(new_user)
            return new_user

        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already registered.",
            ) from exc
        except SQLAlchemyError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register user.",
            ) from exc

    @staticmethod
    def authenticate_user(db: Session, credentials: UserLogin) -> LoginResponse:
        """Verify user credentials and issue signed JWT."""
        normalized_email = credentials.email.strip().lower()
        user = UserRepository.get_by_email(db, normalized_email)
        if not user or not verify_password(
            credentials.password, user.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = create_access_token({"sub": str(user.user_uuid)})
        return LoginResponse(
            message="Login successful",
            user_id=str(user.user_uuid),
            access_token=token,
            token_type="bearer",
        )
