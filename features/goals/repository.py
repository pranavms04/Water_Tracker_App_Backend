"""Settings and hydration goals repository."""

from typing import Optional
from sqlalchemy.orm import Session
from app.features.goals.models import Settings


class SettingsRepository:
    @staticmethod
    def get_by_user_id(db: Session, user_id: int) -> Optional[Settings]:
        """Fetch user settings by user ID."""
        return db.query(Settings).filter(Settings.user_id == user_id).first()

    @staticmethod
    def get_or_create(
        db: Session, user_id: int, default_goal_ml: float = 2500.0
    ) -> Settings:
        """Fetch user settings or initialize default settings if not existing."""
        settings = (
            db.query(Settings).filter(Settings.user_id == user_id).first()
        )
        if not settings:
            settings = Settings(daily_goal_ml=default_goal_ml, user_id=user_id)
            db.add(settings)
            db.commit()
            db.refresh(settings)
        return settings

    @staticmethod
    def update_goal(
        db: Session, user_id: int, daily_goal_ml: float
    ) -> Settings:
        """Update the daily water goal for a given user."""
        settings = SettingsRepository.get_or_create(db, user_id)
        settings.daily_goal_ml = daily_goal_ml
        db.commit()
        db.refresh(settings)
        return settings
