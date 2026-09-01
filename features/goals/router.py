"""Goals and hydration recommendations router."""

from typing import Annotated
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.features.goals.schemas import (
    ClimateEnum,
    GoalRecommendationResponse,
    GoalResponse,
    GoalUpdate,
    SmartGoalRecommendationResponse,
)
from app.features.goals.service import GoalService
from app.features.users.models import User

router = APIRouter(tags=["Goals"])


@router.get(
    "/goals/recommendation",
    response_model=GoalRecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get recommended daily/weekly limits and safe ranges",
)
def get_recommendation(
    climate: ClimateEnum = Query(
        ClimateEnum.TEMPERATE,
        description="Climate condition to adjust water loss",
    ),
    current_user: User = Depends(get_current_user),
) -> dict:
    return GoalService.compute_water_recommendation(
        weight_kg=current_user.weight_kg or 70.0,
        gender=current_user.gender or "other",
        activity_level=current_user.activity_level or "moderate",
        climate=climate.value,
    )


@router.get(
    "/goal",
    response_model=GoalResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the user's active daily and weekly goal",
)
def get_goal(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GoalResponse:
    return GoalService.get_goal(db, current_user.id)


@router.put(
    "/goal",
    response_model=GoalResponse,
    status_code=status.HTTP_200_OK,
    summary="Update daily goal",
)
def update_goal(
    goal_update: GoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GoalResponse:
    return GoalService.update_goal(db, current_user.id, goal_update)


@router.get(
    "/goals/recommendation-by-location",
    response_model=SmartGoalRecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get smart hydration recommendation based on GPS temperature",
)
async def get_recommendation_by_location(
    latitude: Annotated[
        float,
        Query(
            ge=-90.0,
            le=90.0,
            description="User latitude",
            examples=[12.9716],
        ),
    ],
    longitude: Annotated[
        float,
        Query(
            ge=-180.0,
            le=180.0,
            description="User longitude",
            examples=[77.5946],
        ),
    ],
    current_user: User = Depends(get_current_user),
) -> dict:
    current_temp = await GoalService.fetch_temperature_from_coords(
        latitude, longitude
    )
    return GoalService.compute_smart_water_recommendation(
        weight_kg=current_user.weight_kg or 70.0,
        gender=current_user.gender or "other",
        activity_level=current_user.activity_level or "moderate",
        temp_celsius=current_temp,
    )
