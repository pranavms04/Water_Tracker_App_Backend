"""Database package."""

from app.db.base import Base
from app.db.session import engine, SessionLocal, get_db

# Ensure all SQLAlchemy models are registered in the mapper registry
from app.features.users.models import User  # noqa: F401
from app.features.waterlogs.models import WaterLog  # noqa: F401
from app.features.goals.models import Settings  # noqa: F401
from app.features.reminders.models import ReminderSettings  # noqa: F401

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "User",
    "WaterLog",
    "Settings",
    "ReminderSettings",
]

