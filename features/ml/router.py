"""FastAPI router for Machine Learning hydration models and predictions."""

from __future__ import annotations

from typing import Annotated, Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.features.goals.repository import SettingsRepository
from app.features.goals.service import GoalService
from app.features.ml.schemas import (
    DehydrationRiskRequest,
    DehydrationRiskResponse,
    IntakeForecastRequest,
    IntakeForecastResponse,
    MLGoalPredictionRequest,
    MLGoalPredictionResponse,
    MLStatusResponse,
    MLTrainRequest,
    MLTrainResponse,
    SeasonEnum,
    SmartReminderScheduleRequest,
    SmartReminderScheduleResponse,
)
from app.features.ml.service import MLService
from app.features.ml.trainer import train_all_models
from app.features.users.models import User
from app.features.users.schemas import ActivityLevelEnum, GenderEnum
from app.features.waterlogs.service import WaterLogService

router = APIRouter(prefix="/ml", tags=["Machine Learning & AI"])


@router.post(
    "/predict/goal",
    response_model=MLGoalPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict personalized daily hydration goal using Gradient Boosting ML model",
)
def predict_daily_goal(
    req: MLGoalPredictionRequest,
) -> MLGoalPredictionResponse:
    """Predict optimal daily water consumption (ml) considering multi-factorial

    physiology, exercise duration, daily steps, caffeine intake, ambient temperature,
    humidity, and seasonal climate variation.
    """
    return MLService.predict_daily_goal(req)


@router.post(
    "/predict/risk",
    response_model=DehydrationRiskResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict real-time dehydration risk level and immediate hydration advice",
)
def predict_dehydration_risk(
    req: DehydrationRiskRequest,
) -> DehydrationRiskResponse:
    """Assess intraday dehydration risk (low, moderate, high), probability breakdown,

    hourly pace ratio, and personalized corrective actions.
    """
    return MLService.predict_dehydration_risk(req)


@router.post(
    "/predict/reminders",
    response_model=SmartReminderScheduleResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate circadian-aligned smart hydration reminder schedule",
)
def generate_smart_reminders(
    req: SmartReminderScheduleRequest,
) -> SmartReminderScheduleResponse:
    """Generate dynamic reminder schedule distributed smoothly across waking hours

    with nocturnal tapering.
    """
    return MLService.generate_smart_reminder_schedule(req)


@router.post(
    "/predict/forecast",
    response_model=IntakeForecastResponse,
    status_code=status.HTTP_200_OK,
    summary="Forecast cumulative intake trajectory through 23:59",
)
def forecast_intake_trajectory(
    req: IntakeForecastRequest,
) -> IntakeForecastResponse:
    """Forecast end-of-day total volume and projected milestone trajectory based on

    current progress and historical habits.
    """
    return MLService.forecast_intake_trajectory(req)


@router.get(
    "/recommendation/me",
    response_model=MLGoalPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Compute ML hydration recommendation for current authenticated user",
)
async def get_user_ml_recommendation(
    latitude: Annotated[
        Optional[float],
        Query(ge=-90.0, le=90.0, description="Optional GPS latitude for live weather"),
    ] = None,
    longitude: Annotated[
        Optional[float],
        Query(
            ge=-180.0, le=180.0, description="Optional GPS longitude for live weather"
        ),
    ] = None,
    exercise_duration_min: Annotated[
        float,
        Query(ge=0.0, le=360.0, description="Workout duration in minutes"),
    ] = 0.0,
    daily_steps: Annotated[
        int,
        Query(ge=0, le=60000, description="Step count for today"),
    ] = 6000,
    caffeine_intake_mg: Annotated[
        float,
        Query(ge=0.0, le=1000.0, description="Caffeine consumed in mg"),
    ] = 0.0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MLGoalPredictionResponse:
    """Compute an end-to-end personalized ML recommendation using the current user's

    profile (weight, gender, activity tier) and optional live ambient weather from
    Open-Meteo.
    """
    if (latitude is not None and longitude is None) or (latitude is None and longitude is not None):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Both latitude and longitude must be provided together for location-based weather.",
        )

    temp_c = 22.0
    if latitude is not None and longitude is not None:
        temp_c = await GoalService.fetch_temperature_from_coords(
            latitude, longitude
        )

    # Safe enum parsing
    user_gender = GenderEnum.OTHER
    if current_user.gender:
        try:
            user_gender = GenderEnum(current_user.gender)
        except ValueError:
            user_gender = GenderEnum.OTHER

    user_act = ActivityLevelEnum.MODERATE
    if current_user.activity_level:
        try:
            user_act = ActivityLevelEnum(current_user.activity_level)
        except ValueError:
            user_act = ActivityLevelEnum.MODERATE

    req = MLGoalPredictionRequest(
        weight_kg=current_user.weight_kg or 70.0,
        age=28,
        gender=user_gender,
        activity_level=user_act,
        exercise_duration_min=exercise_duration_min,
        daily_steps=daily_steps,
        caffeine_intake_mg=caffeine_intake_mg,
        ambient_temp_c=temp_c,
        humidity_pct=50.0,
        season=SeasonEnum.SUMMER,
        past_adherence_rate=0.85,
        streak_days=0,
    )
    return MLService.predict_daily_goal(req)


@router.post(
    "/train",
    response_model=MLTrainResponse,
    status_code=status.HTTP_200_OK,
    summary="Train or retrain all 4 ML models on synthetic physiological datasets",
)
def train_models(
    req: MLTrainRequest,
) -> MLTrainResponse:
    """Execute model training pipeline across all 4 machine learning models and

    refresh in-memory model instances.
    """
    training_results = train_all_models(
        n_samples=req.n_samples, save_artifacts=True
    )
    MLService.load_models(force_reload=True)

    return MLTrainResponse(
        success=True,
        message=f"Successfully trained 4 ML models with {req.n_samples} samples.",
        trained_at=training_results.get("trained_at", ""),
        n_samples=req.n_samples,
        models=training_results.get("models", {}),
    )


@router.get(
    "/status",
    response_model=MLStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get status of ML engine, loaded models, and artifact paths",
)
def get_ml_status() -> MLStatusResponse:
    """Return runtime readiness and loaded models in memory."""
    return MLService.get_status()


@router.get(
    "/metrics",
    status_code=status.HTTP_200_OK,
    summary="Get cross-validated evaluation metrics and feature importances",
)
def get_ml_metrics() -> dict[str, Any]:
    """Return R2 scores, MAE, accuracy, precision, recall, and feature ranking for

    active models.
    """
    return MLService.get_metrics()
