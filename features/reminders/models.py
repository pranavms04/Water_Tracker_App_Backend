"""Reminder settings SQLAlchemy model."""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class ReminderSettings(Base):
    __tablename__ = "reminder_settings"

    id = Column(Integer, primary_key=True, index=True)
    enabled = Column(Boolean, default=True, nullable=False)
    interval_minutes = Column(Integer, default=120, nullable=False)
    start_time = Column(String, default="08:00", nullable=False)
    end_time = Column(String, default="22:00", nullable=False)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    owner = relationship("User", back_populates="reminder_settings")
