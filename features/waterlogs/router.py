"""Water intake logs router."""

from datetime import date
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.features.users.models import User
from app.features.waterlogs.models import WaterLog
from app.features.waterlogs.schemas import (
    PRESET_AMOUNTS,
    QuickLogCreate,
    TodaySummary,
    WaterLogCreate,
    WaterLogResponse,
    WaterLogUpdate,
)
from app.features.waterlogs.service import WaterLogService

router = APIRouter(prefix="/waterlogs", tags=["Water Logs"])


@router.get(
    "/today",
    response_model=TodaySummary,
    status_code=status.HTTP_200_OK,
    summary="Get today's hydration intake summary against daily goal",
)
def get_today_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TodaySummary:
    return WaterLogService.get_today_summary(db, current_user.id)


@router.post(
    "",
    response_model=WaterLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record new water intake log",
)
def create_waterlog(
    log: WaterLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WaterLog:
    return WaterLogService.create_log(db, current_user.id, log)


@router.post(
    "/quick",
    response_model=WaterLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Quickly record water intake using predefined container sizes",
)
def quick_create_waterlog(
    quick_in: QuickLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WaterLog:
    amount = PRESET_AMOUNTS.get(quick_in.preset, 250.0)
    log_create = WaterLogCreate(amount_ml=amount)
    return WaterLogService.create_log(db, current_user.id, log_create)


@router.get(
    "",
    response_model=List[WaterLogResponse],
    status_code=status.HTTP_200_OK,
    summary="List paginated water intake logs with optional date range filter",
)
def list_waterlogs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="Number of logs to return (1-100)"),
    ] = 50,
    offset: Annotated[
        int,
        Query(ge=0, description="Number of logs to skip"),
    ] = 0,
    start_date: Annotated[
        Optional[date],
        Query(description="Filter logs from this date onward (YYYY-MM-DD)"),
    ] = None,
    end_date: Annotated[
        Optional[date],
        Query(description="Filter logs up to this date (YYYY-MM-DD)"),
    ] = None,
) -> List[WaterLog]:
    return WaterLogService.list_logs(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        start_date=start_date,
        end_date=end_date,
    )


@router.put(
    "/{log_id}",
    response_model=WaterLogResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an existing water intake log",
)
def update_waterlog(
    log_id: Annotated[
        int, Path(gt=0, description="ID of the water log entry")
    ],
    log_update: WaterLogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WaterLog:
    return WaterLogService.update_log(
        db, log_id=log_id, user_id=current_user.id, log_update=log_update
    )


@router.delete(
    "/{log_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a water intake log entry",
)
def delete_waterlog(
    log_id: Annotated[
        int, Path(gt=0, description="ID of the water log entry")
    ],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    WaterLogService.delete_log(db, log_id=log_id, user_id=current_user.id)
    return None
