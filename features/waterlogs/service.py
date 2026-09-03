"""WaterLog business logic service."""

from datetime import date, datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.features.goals.repository import SettingsRepository
from app.features.waterlogs.models import WaterLog
from app.features.waterlogs.repository import WaterLogRepository
from app.features.waterlogs.schemas import TodaySummary, WaterLogCreate, WaterLogUpdate


class WaterLogService:
    @staticmethod
    def create_log(
        db: Session, user_id: int, log_in: WaterLogCreate
    ) -> WaterLog:
        """Record water intake with error handling."""
        try:
            return WaterLogRepository.create(
                db,
                user_id=user_id,
                amount_ml=log_in.amount_ml,
                logged_at=log_in.logged_at,
            )
        except SQLAlchemyError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to record water intake.",
            ) from exc

    @staticmethod
    def list_logs(
        db: Session,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[WaterLog]:
        """List water logs with range validation and error handling."""
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="start_date cannot be later than end_date.",
            )

        try:
            return WaterLogRepository.list_by_user(
                db,
                user_id=user_id,
                limit=limit,
                offset=offset,
                start_date=start_date,
                end_date=end_date,
            )
        except SQLAlchemyError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve water logs.",
            ) from exc

    @staticmethod
    def update_log(
        db: Session, log_id: int, user_id: int, log_update: WaterLogUpdate
    ) -> WaterLog:
        """Update water log amount with existence validation."""
        existing = WaterLogRepository.get_by_id(db, log_id, user_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Water log entry not found.",
            )

        try:
            updated = WaterLogRepository.update(
                db, log_id, user_id, log_update.amount_ml
            )
            return updated
        except SQLAlchemyError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update water log entry.",
            ) from exc

    @staticmethod
    def delete_log(db: Session, log_id: int, user_id: int) -> None:
        """Delete water log with existence validation."""
        existing = WaterLogRepository.get_by_id(db, log_id, user_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Water log entry not found.",
            )

        try:
            WaterLogRepository.delete(db, log_id, user_id)
        except SQLAlchemyError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete water log entry.",
            ) from exc

    @staticmethod
    def get_today_summary(db: Session, user_id: int) -> TodaySummary:
        """Compute today's hydration intake vs target goal."""
        goal_settings = SettingsRepository.get_or_create(db, user_id)
        goal = goal_settings.daily_goal_ml
        today = datetime.now(timezone.utc).date()

        logs = WaterLogRepository.get_all_by_user(db, user_id)
        total_today = sum(
            log.amount_ml
            for log in logs
            if (log.logged_at.date() if hasattr(log.logged_at, "date") else log.logged_at) == today
        )

        remaining = max(goal - total_today, 0.0)
        percent = round(min(total_today / goal, 1.0) * 100, 1) if goal > 0 else 0.0

        return TodaySummary(
            total_ml=round(total_today, 1),
            goal_ml=round(goal, 1),
            remaining_ml=round(remaining, 1),
            percent_complete=percent,
        )
