"""Pydantic schemas for hydration analytics and streaks."""

from typing import Dict
from pydantic import BaseModel


class StatsResponse(BaseModel):
    daily_average_ml: float
    current_streak_days: int
    longest_streak_days: int
    hourly_breakdown: Dict[int, float]


class WeeklyTrendResponse(BaseModel):
    trend: Dict[str, float]
