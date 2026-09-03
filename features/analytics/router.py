from datetime import date, datetime, timezone
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.features.analytics.pdf_service import PDFReportService
from app.features.analytics.schemas import StatsResponse
from app.features.analytics.service import AnalyticsService
from app.features.users.models import User

router = APIRouter(prefix="/stats", tags=["Analytics"])


@router.get(
    "",
    response_model=StatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user hydration statistics, streak counts, and hourly trends",
)
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    return AnalyticsService.get_stats(db, current_user.id)


@router.get(
    "/weekly",
    status_code=status.HTTP_200_OK,
    summary="Get 7-day hydration consumption trend",
)
def get_weekly_trend(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, float]:
    return AnalyticsService.get_weekly_trend(db, current_user.id)


@router.get(
    "/report/pdf",
    status_code=status.HTTP_200_OK,
    summary="Download user water intake summary report as PDF",
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Returns the generated PDF hydration summary report.",
        }
    },
)
def download_intake_report_pdf(
    start_date: Optional[date] = Query(None, description="Start date for report range (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for report range (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Generate and stream a formatted PDF hydration summary report."""
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be later than end_date.",
        )

    pdf_buffer = PDFReportService.generate_intake_report_pdf(
        db=db,
        user=current_user,
        start_date=start_date,
        end_date=end_date,
    )
    
    effective_end = end_date or datetime.now(timezone.utc).date()
    filename = f"watertrack_summary_{effective_end.isoformat()}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )

