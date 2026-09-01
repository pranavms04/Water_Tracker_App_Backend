"""Reminder settings business logic service."""

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.features.reminders.models import ReminderSettings
from app.features.reminders.repository import ReminderRepository
from app.features.reminders.schemas import ReminderSettingsUpdate


class ReminderService:
    @staticmethod
    def get_reminders(db: Session, user_id: int) -> ReminderSettings:
        """Fetch or initialize default reminder settings for user."""
        try:
            return ReminderRepository.get_or_create(db, user_id)
        except SQLAlchemyError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve reminder settings.",
            ) from exc

    @staticmethod
    def update_reminders(
        db: Session, user_id: int, update: ReminderSettingsUpdate
    ) -> ReminderSettings:
        """Update reminder settings with validation and rollback safety."""
        if (
            update.start_time
            and update.end_time
            and update.start_time >= update.end_time
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Reminder start_time must be earlier than end_time.",
            )

        try:
            return ReminderRepository.update(db, user_id, update)
        except SQLAlchemyError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update reminder settings.",
            ) from exc
