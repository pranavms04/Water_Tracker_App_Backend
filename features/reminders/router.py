"""Reminder settings router."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.features.reminders.models import ReminderSettings
from app.features.reminders.schemas import (
    ReminderSettingsResponse,
    ReminderSettingsUpdate,
)
from app.features.reminders.service import ReminderService
from app.features.users.models import User

router = APIRouter(prefix="/reminders", tags=["Reminders"])


@router.get(
    "",
    response_model=ReminderSettingsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user hydration reminder settings",
)
def get_reminders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReminderSettings:
    return ReminderService.get_reminders(db, current_user.id)


@router.put(
    "",
    response_model=ReminderSettingsResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user hydration reminder settings",
)
def update_reminders(
    update: ReminderSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReminderSettings:
    return ReminderService.update_reminders(db, current_user.id, update)
