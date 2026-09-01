"""User SQLAlchemy ORM model."""

from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_uuid = Column(
        String(36),
        unique=True,
        index=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String(100), nullable=False)
    weight_kg = Column(Float, nullable=True)
    gender = Column(String(20), default="other", nullable=True)
    activity_level = Column(String(30), default="moderate", nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    water_logs = relationship(
        "WaterLog",
        back_populates="owner",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    settings = relationship(
        "Settings",
        back_populates="owner",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    reminder_settings = relationship(
        "ReminderSettings",
        back_populates="owner",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


# Ensure related models are registered with declarative base
import app.features.waterlogs.models  # noqa: F401, E402
import app.features.goals.models  # noqa: F401, E402
import app.features.reminders.models  # noqa: F401, E402

