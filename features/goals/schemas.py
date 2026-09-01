"""Pydantic schemas for goals and hydration recommendations."""

from enum import Enum
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class ClimateEnum(str, Enum):
    COLD = "cold"
    TEMPERATE = "temperate"
    HOT = "hot"
    VERY_HOT = "very_hot"


class GoalUpdate(BaseModel):
    daily_goal_ml: float = Field(
        ...,
        ge=500.0,
        le=10000.0,
        description="Target daily water intake in milliliters (500 to 10,000 ml)",
    )


class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    daily_goal_ml: float
    weekly_goal_ml: float


class GoalRecommendationResponse(BaseModel):
    recommended_daily_ml: float
    min_safe_limit_ml: float
    max_safe_limit_ml: float
    recommended_weekly_ml: float
    breakdown: Dict[str, Any]


class WeatherDetails(BaseModel):
    current_temperature_celsius: float
    condition: str
    weather_fluid_adjustment_ml: float


class SmartGoalRecommendationResponse(BaseModel):
    recommended_daily_ml: float
    min_safe_limit_ml: float
    max_safe_limit_ml: float
    recommended_weekly_ml: float
    weather_data: WeatherDetails
    breakdown: Dict[str, Any]
