"""Goals feature package."""

from app.features.goals.models import Settings
from app.features.goals.schemas import (
    ClimateEnum,
    GoalRecommendationResponse,
    GoalResponse,
    GoalUpdate,
    SmartGoalRecommendationResponse,
    WeatherDetails,
)
from app.features.goals.repository import SettingsRepository
from app.features.goals.service import GoalService

__all__ = [
    "Settings",
    "ClimateEnum",
    "GoalResponse",
    "GoalUpdate",
    "GoalRecommendationResponse",
    "SmartGoalRecommendationResponse",
    "WeatherDetails",
    "SettingsRepository",
    "GoalService",
]
