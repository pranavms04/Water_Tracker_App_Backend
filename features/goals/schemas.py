"""Pydantic schemas for goals and hydration recommendations."""

import math
from enum import Enum
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


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

    @field_validator("daily_goal_ml")
    @classmethod
    def validate_goal(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            raise ValueError("daily_goal_ml must be a valid finite number")
        return v


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
