"""Pydantic v2 schemas for Machine Learning models and inference endpoints."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.features.users.schemas import ActivityLevelEnum, GenderEnum


class SeasonEnum(str, Enum):
    WINTER = "winter"
    SPRING = "spring"
    SUMMER = "summer"
    FALL = "fall"


class FactorImpact(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    factor: str = Field(description="Name of the physiological or environmental factor")
    impact_ml: float = Field(description="Contribution in milliliters")
    description: str = Field(description="Human-readable explanation of the adjustment")


class MLGoalPredictionRequest(BaseModel):
    weight_kg: float = Field(..., gt=20.0, le=300.0, description="User body weight in kg")
    age: int = Field(default=28, ge=10, le=100, description="User age in years")
    gender: GenderEnum = Field(default=GenderEnum.OTHER, description="User biological sex/gender")
    activity_level: ActivityLevelEnum = Field(
        default=ActivityLevelEnum.MODERATE, description="General physical activity tier"
    )
    exercise_duration_min: float = Field(
        default=0.0, ge=0.0, le=360.0, description="Daily planned or completed workout minutes"
    )
    daily_steps: int = Field(
        default=6000, ge=0, le=60000, description="Estimated or tracked daily step count"
    )
    caffeine_intake_mg: float = Field(
        default=0.0, ge=0.0, le=1000.0, description="Daily caffeine consumption in mg"
    )
    ambient_temp_c: float = Field(
        default=22.0, ge=-25.0, le=60.0, description="Ambient temperature in Celsius"
    )
    humidity_pct: float = Field(
        default=50.0, ge=5.0, le=100.0, description="Relative humidity percentage"
    )
    season: SeasonEnum = Field(default=SeasonEnum.SUMMER, description="Current season")
    past_adherence_rate: float = Field(
        default=0.80, ge=0.0, le=1.0, description="Historical goal completion fraction (0-1)"
    )
    streak_days: int = Field(default=0, ge=0, le=3650, description="Current consecutive goal streak days")


class MLGoalPredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    predicted_goal_ml: float = Field(description="ML-predicted optimal daily hydration target in ml")
    min_safe_ml: float = Field(description="Minimum physiological safety floor")
    max_safe_ml: float = Field(description="Maximum physiological safety ceiling")
    confidence_score: float = Field(description="Model prediction confidence score (0-1)")
    formula_breakdown: List[FactorImpact] = Field(
        description="Factor contributions to the target volume"
    )
    model_version: str = Field(default="1.0.0", description="ML model version")
    model_type: str = Field(
        default="GradientBoostingRegressor", description="Scikit-learn model architecture"
    )


class DehydrationRiskRequest(BaseModel):
    weight_kg: float = Field(..., gt=20.0, le=300.0, description="User body weight in kg")
    age: int = Field(default=28, ge=10, le=100)
    gender: GenderEnum = Field(default=GenderEnum.OTHER)
    activity_level: ActivityLevelEnum = Field(default=ActivityLevelEnum.MODERATE)
    exercise_duration_min: float = Field(default=0.0, ge=0.0, le=360.0)
    daily_steps: int = Field(default=5000, ge=0, le=60000)
    ambient_temp_c: float = Field(default=24.0, ge=-25.0, le=60.0)
    humidity_pct: float = Field(default=50.0, ge=5.0, le=100.0)
    current_hour: int = Field(..., ge=0, le=23, description="Current hour of the day (0-23)")
    intake_so_far_ml: float = Field(..., ge=0.0, le=20000.0, description="Water consumed so far today in ml")
    daily_goal_ml: float = Field(..., ge=500.0, le=10000.0, description="Active daily goal in ml")
    hours_since_last_drink: float = Field(
        default=1.5, ge=0.0, le=24.0, description="Elapsed hours since the last recorded drink"
    )
    streak_days: int = Field(default=0, ge=0, le=3650)


class DehydrationRiskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    risk_level: str = Field(description="'low' (optimal), 'moderate', or 'high' dehydration risk")
    risk_score: float = Field(description="Dehydration index from 0.0 (safe) to 100.0 (severe)")
    risk_probabilities: Dict[str, float] = Field(
        description="Model class probabilities for each risk tier"
    )
    current_pace_ratio: float = Field(
        description="Intake progress divided by scheduled expectation (>1.0 is ahead, <1.0 is behind)"
    )
    recommended_immediate_intake_ml: float = Field(
        description="Suggested immediate water consumption in ml"
    )
    next_reminder_in_minutes: int = Field(
        description="Recommended delay until the next hydration prompt"
    )
    actionable_guidance: str = Field(description="Personalized contextual hydration advice")


class ReminderSlot(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    time: str = Field(description="Scheduled time in HH:MM format")
    recommended_amount_ml: float = Field(description="Target volume for this reminder in ml")
    reason: str = Field(description="Contextual physiological reason for this reminder")


class SmartReminderScheduleRequest(BaseModel):
    start_time: str = Field(default="08:00", description="Wake / active start time (HH:MM)")
    end_time: str = Field(default="22:00", description="Sleep / active end time (HH:MM)")
    daily_goal_ml: float = Field(..., ge=500.0, le=10000.0, description="Target daily water intake")
    intake_so_far_ml: float = Field(default=0.0, ge=0.0, le=20000.0, description="Consumed volume today")
    weight_kg: float = Field(default=70.0, gt=20.0, le=300.0)
    ambient_temp_c: float = Field(default=24.0, ge=-25.0, le=60.0)
    activity_level: ActivityLevelEnum = Field(default=ActivityLevelEnum.MODERATE)

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        parts = v.split(":")
        if len(parts) != 2:
            raise ValueError("Time must be in HH:MM format")
        try:
            h, m = int(parts[0]), int(parts[1])
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError
        except ValueError:
            raise ValueError("Invalid hour or minute in HH:MM time string")
        return v

    @field_validator("end_time")
    @classmethod
    def end_after_start(cls, v: str, info) -> str:
        start = info.data.get("start_time")
        if start and v <= start:
            raise ValueError("end_time must be strictly after start_time")
        return v


class SmartReminderScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    daily_goal_ml: float
    intake_so_far_ml: float
    remaining_ml: float
    total_slots: int
    schedule_mode: str = "adaptive_ml"
    slots: List[ReminderSlot]


class IntakeForecastRequest(BaseModel):
    weight_kg: float = Field(default=70.0, gt=20.0, le=300.0)
    ambient_temp_c: float = Field(default=24.0, ge=-25.0, le=60.0)
    current_hour: int = Field(..., ge=0, le=23)
    intake_so_far_ml: float = Field(..., ge=0.0, le=20000.0)
    daily_goal_ml: float = Field(..., ge=500.0, le=10000.0)
    past_adherence_rate: float = Field(default=0.80, ge=0.0, le=1.0)
    streak_days: int = Field(default=0, ge=0, le=3650)
    activity_level: ActivityLevelEnum = Field(default=ActivityLevelEnum.MODERATE)


class HourlyTrajectoryPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    hour: int
    time_label: str
    projected_cumulative_ml: float
    is_past: bool


class IntakeForecastResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    predicted_end_of_day_ml: float = Field(
        description="ML-forecasted total water intake by 23:59"
    )
    daily_goal_ml: float
    projected_achievement_pct: float
    on_track: bool
    trajectory: List[HourlyTrajectoryPoint]
    nudge_message: str


class MLTrainRequest(BaseModel):
    n_samples: int = Field(
        default=5000,
        ge=500,
        le=20000,
        description="Number of synthetic physiological samples to train on",
    )


class MLTrainResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    success: bool
    message: str
    trained_at: str
    n_samples: int
    models: Dict[str, Any]


class MLStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    engine: str
    models_loaded: Dict[str, bool]
    last_trained_at: Optional[str] = None
    artifacts_directory: str
