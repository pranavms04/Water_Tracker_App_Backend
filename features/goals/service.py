"""Goal calculation and weather integration service."""

from typing import Any, Dict, Tuple
import httpx
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings as app_settings
from app.core.logging import logger
from app.features.goals.models import Settings
from app.features.goals.repository import SettingsRepository
from app.features.goals.schemas import (
    GoalRecommendationResponse,
    GoalResponse,
    GoalUpdate,
    SmartGoalRecommendationResponse,
    WeatherDetails,
)


class GoalService:
    @staticmethod
    def get_goal(db: Session, user_id: int) -> GoalResponse:
        """Fetch current user's daily and weekly goal."""
        settings = SettingsRepository.get_or_create(db, user_id)
        return GoalResponse(
            daily_goal_ml=settings.daily_goal_ml,
            weekly_goal_ml=settings.daily_goal_ml * 7,
        )

    @staticmethod
    def update_goal(
        db: Session, user_id: int, goal_update: GoalUpdate
    ) -> GoalResponse:
        """Update user's daily goal."""
        try:
            settings = SettingsRepository.update_goal(
                db, user_id, goal_update.daily_goal_ml
            )
            return GoalResponse(
                daily_goal_ml=settings.daily_goal_ml,
                weekly_goal_ml=settings.daily_goal_ml * 7,
            )
        except SQLAlchemyError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update goal.",
            ) from exc

    @staticmethod
    def compute_water_recommendation(
        weight_kg: float = 70.0,
        gender: str = "other",
        activity_level: str = "moderate",
        climate: str = "temperate",
    ) -> Dict[str, Any]:
        """Calculates personalized hydration recommendation with safety bounds."""
        base_ml = weight_kg * app_settings.BASE_ML_PER_KG

        gender_adj = (
            200.0 if gender == "male" else (-100.0 if gender == "female" else 0.0)
        )

        activity_map = {
            "sedentary": 0.0,
            "light": 300.0,
            "moderate": 600.0,
            "very_active": 1000.0,
        }
        activity_adj = activity_map.get(activity_level, 300.0)

        climate_map = {
            "cold": -100.0,
            "temperate": 0.0,
            "hot": 400.0,
            "very_hot": 750.0,
        }
        climate_adj = climate_map.get(climate, 0.0)

        raw_daily = base_ml + gender_adj + activity_adj + climate_adj
        min_safe = round(
            max(weight_kg * app_settings.MIN_SAFE_FACTOR, app_settings.MIN_SAFE_FLOOR_ML),
            -1,
        )
        max_safe = round(
            min(weight_kg * app_settings.MAX_SAFE_FACTOR, app_settings.MAX_SAFE_CEILING_ML),
            -1,
        )

        recommended_daily = round(min(max(raw_daily, min_safe), max_safe), -1)

        return {
            "recommended_daily_ml": recommended_daily,
            "min_safe_limit_ml": min_safe,
            "max_safe_limit_ml": max_safe,
            "recommended_weekly_ml": recommended_daily * 7,
            "breakdown": {
                "base_from_weight": base_ml,
                "gender_adjustment": gender_adj,
                "activity_adjustment": activity_adj,
                "climate_adjustment": climate_adj,
            },
        }

    @staticmethod
    def calculate_temp_water_adjustment(
        temp_celsius: float,
    ) -> Tuple[float, str]:
        """Determine fluid adjustment and weather description based on ambient temperature."""
        if temp_celsius < 15.0:
            return -100.0, "Cold"
        elif temp_celsius <= 25.0:
            return 0.0, "Mild / Comfortable"
        elif temp_celsius <= 32.0:
            return 300.0, "Warm"
        elif temp_celsius <= 38.0:
            return 600.0, "Hot"
        else:
            return 900.0, "Extreme Heat"

    @staticmethod
    async def fetch_temperature_from_coords(
        latitude: float, longitude: float
    ) -> float:
        """Fetch real-time temperature (°C) for GPS coordinates via Open-Meteo with timeout fallback."""
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m",
        }
        try:
            async with httpx.AsyncClient(
                timeout=app_settings.OPEN_METEO_TIMEOUT_SECONDS
            ) as client:
                response = await client.get(
                    app_settings.OPEN_METEO_BASE_URL, params=params
                )
                if response.status_code == 200:
                    data = response.json()
                    return float(data["current"]["temperature_2m"])
                logger.warning(
                    f"Open-Meteo returned status {response.status_code}, using fallback."
                )
        except Exception as exc:
            logger.warning(
                f"Failed to fetch weather from Open-Meteo ({exc}), using fallback {app_settings.DEFAULT_ROOM_TEMP_CELSIUS}°C."
            )

        return app_settings.DEFAULT_ROOM_TEMP_CELSIUS

    @staticmethod
    def compute_smart_water_recommendation(
        weight_kg: float = 70.0,
        gender: str = "other",
        activity_level: str = "moderate",
        temp_celsius: float = 22.0,
    ) -> Dict[str, Any]:
        """Calculates personalized hydration recommendation adjusted for live ambient temperature."""
        base_ml = weight_kg * app_settings.BASE_ML_PER_KG

        gender_adj = (
            200.0 if gender == "male" else (-100.0 if gender == "female" else 0.0)
        )

        activity_map = {
            "sedentary": 0.0,
            "light": 300.0,
            "moderate": 600.0,
            "very_active": 1000.0,
        }
        activity_adj = activity_map.get(activity_level, 300.0)

        temp_adj, temp_category = GoalService.calculate_temp_water_adjustment(
            temp_celsius
        )

        raw_daily = base_ml + gender_adj + activity_adj + temp_adj
        min_safe = round(
            max(weight_kg * app_settings.MIN_SAFE_FACTOR, app_settings.MIN_SAFE_FLOOR_ML),
            -1,
        )
        max_safe = round(
            min(weight_kg * app_settings.MAX_SAFE_FACTOR, app_settings.MAX_SAFE_CEILING_ML),
            -1,
        )

        recommended_daily = round(min(max(raw_daily, min_safe), max_safe), -1)

        return {
            "recommended_daily_ml": recommended_daily,
            "min_safe_limit_ml": min_safe,
            "max_safe_limit_ml": max_safe,
            "recommended_weekly_ml": recommended_daily * 7,
            "weather_data": {
                "current_temperature_celsius": temp_celsius,
                "condition": temp_category,
                "weather_fluid_adjustment_ml": temp_adj,
            },
            "breakdown": {
                "base_from_weight": base_ml,
                "gender_adjustment": gender_adj,
                "activity_adjustment": activity_adj,
                "temperature_adjustment": temp_adj,
            },
        }
