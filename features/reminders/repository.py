"""Reminder settings repository data access layer."""

from typing import Optional
from sqlalchemy.orm import Session
from app.features.reminders.models import ReminderSettings
from app.features.reminders.schemas import ReminderSettingsUpdate


class ReminderRepository:
    @staticmethod
    def get_by_user_id(
        db: Session, user_id: int
    ) -> Optional[ReminderSettings]:
        """Fetch reminder configuration for user."""
        return (
            db.query(ReminderSettings)
            .filter(ReminderSettings.user_id == user_id)
            .first()
        )

    @staticmethod
    def get_or_create(db: Session, user_id: int) -> ReminderSettings:
        """Fetch or create default reminder configuration for user."""
        settings = (
            db.query(ReminderSettings)
            .filter(ReminderSettings.user_id == user_id)
            .first()
        )
        if not settings:
            settings = ReminderSettings(user_id=user_id)
            db.add(settings)
            db.commit()
            db.refresh(settings)
        return settings

    @staticmethod
    def update(
        db: Session, user_id: int, update_data: ReminderSettingsUpdate
    ) -> ReminderSettings:
        """Update reminder configuration fields."""
        settings = ReminderRepository.get_or_create(db, user_id)
        settings.enabled = update_data.enabled
        settings.interval_minutes = update_data.interval_minutes
        settings.start_time = update_data.start_time
        settings.end_time = update_data.end_time
        db.commit()
        db.refresh(settings)
        return settings
