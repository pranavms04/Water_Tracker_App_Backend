"""WaterLog repository data access layer."""

from datetime import date, datetime, time, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from app.features.waterlogs.models import WaterLog


class WaterLogRepository:
    @staticmethod
    def create(
        db: Session,
        user_id: int,
        amount_ml: float,
        logged_at: Optional[datetime] = None,
    ) -> WaterLog:
        """Create and persist a new water intake record."""
        log = WaterLog(
            amount_ml=amount_ml,
            user_id=user_id,
            logged_at=logged_at or datetime.now(timezone.utc),
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def get_by_id(
        db: Session, log_id: int, user_id: int
    ) -> Optional[WaterLog]:
        """Fetch a specific water log record belonging to a user."""
        return (
            db.query(WaterLog)
            .filter(WaterLog.id == log_id, WaterLog.user_id == user_id)
            .first()
        )

    @staticmethod
    def list_by_user(
        db: Session,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[WaterLog]:
        """Query paginated water logs for a user with optional date boundary filtering."""
        query = db.query(WaterLog).filter(WaterLog.user_id == user_id)

        if start_date:
            start_dt = datetime.combine(
                start_date, time.min, tzinfo=timezone.utc
            )
            query = query.filter(WaterLog.logged_at >= start_dt)

        if end_date:
            end_dt = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
            query = query.filter(WaterLog.logged_at <= end_dt)

        return (
            query.order_by(WaterLog.logged_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_all_by_user(db: Session, user_id: int) -> List[WaterLog]:
        """Retrieve all water intake entries recorded by a user."""
        return (
            db.query(WaterLog)
            .filter(WaterLog.user_id == user_id)
            .order_by(WaterLog.logged_at.asc())
            .all()
        )

    @staticmethod
    def update(
        db: Session, log_id: int, user_id: int, amount_ml: float
    ) -> Optional[WaterLog]:
        """Update amount for an existing water log."""
        log = WaterLogRepository.get_by_id(db, log_id, user_id)
        if not log:
            return None
        log.amount_ml = amount_ml
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def delete(db: Session, log_id: int, user_id: int) -> bool:
        """Delete an existing water log."""
        log = WaterLogRepository.get_by_id(db, log_id, user_id)
        if not log:
            return False
        db.delete(log)
        db.commit()
        return True
