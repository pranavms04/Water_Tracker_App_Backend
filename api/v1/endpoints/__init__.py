"""API v1 Endpoints module exports."""

from app.features.auth.router import router as auth_router
from app.features.users.router import router as users_router
from app.features.waterlogs.router import router as waterlogs_router
from app.features.goals.router import router as goals_router
from app.features.reminders.router import router as reminders_router
from app.features.analytics.router import router as analytics_router

__all__ = [
    "auth_router",
    "users_router",
    "waterlogs_router",
    "goals_router",
    "reminders_router",
    "analytics_router",
]
