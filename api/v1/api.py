"""Centralized API v1 router definition."""

from fastapi import APIRouter

from app.features.auth.router import router as auth_router
from app.features.users.router import router as users_router
from app.features.waterlogs.router import router as waterlogs_router
from app.features.goals.router import router as goals_router
from app.features.reminders.router import router as reminders_router
from app.features.analytics.router import router as analytics_router
from app.features.ml.router import router as ml_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(waterlogs_router)
api_router.include_router(goals_router)
api_router.include_router(reminders_router)
api_router.include_router(analytics_router)
api_router.include_router(ml_router)
