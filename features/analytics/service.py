"""Analytics and streak calculation service with true calendar continuity."""

from datetime import date, timedelta
from typing import Any, Dict
import pandas as pd
from sqlalchemy.orm import Session

from app.features.goals.repository import SettingsRepository
from app.features.waterlogs.repository import WaterLogRepository


class AnalyticsService:
    @staticmethod
    def get_stats(db: Session, user_id: int) -> Dict[str, Any]:
        """Calculates hydration statistics, streaks with calendar continuity, and hourly breakdowns."""
        goal = SettingsRepository.get_or_create(db, user_id).daily_goal_ml
        logs = WaterLogRepository.get_all_by_user(db, user_id)

        if not logs:
            return {
                "daily_average_ml": 0.0,
                "current_streak_days": 0,
                "longest_streak_days": 0,
                "hourly_breakdown": {},
            }

        df = pd.DataFrame(
            [{"amount_ml": l.amount_ml, "logged_at": l.logged_at} for l in logs]
        )
        df["logged_at"] = pd.to_datetime(df["logged_at"])
        df["date"] = df["logged_at"].dt.date
        df["hour"] = df["logged_at"].dt.hour

        daily_totals = df.groupby("date")["amount_ml"].sum().to_dict()
        daily_average_ml = round(float(pd.Series(daily_totals).mean()), 1)

        # Build calendar continuity for streak calculation
        min_date = min(daily_totals.keys())
        today = date.today()
        total_days = (today - min_date).days + 1

        calendar_dates = [min_date + timedelta(days=i) for i in range(total_days)]
        daily_goal_met = {d: daily_totals.get(d, 0.0) >= goal for d in calendar_dates}

        # Calculate longest streak across full calendar timeline
        longest_streak = 0
        running_streak = 0
        for d in calendar_dates:
            if daily_goal_met[d]:
                running_streak += 1
                longest_streak = max(longest_streak, running_streak)
            else:
                running_streak = 0

        # Calculate current streak:
        # Check today first; if met, count consecutive days back.
        # If today is not yet met (still in progress), check if yesterday was met and count back from yesterday.
        current_streak = 0
        start_check = today
        if not daily_goal_met.get(today, False):
            start_check = today - timedelta(days=1)

        check_date = start_check
        while check_date >= min_date and daily_goal_met.get(check_date, False):
            current_streak += 1
            check_date -= timedelta(days=1)

        hourly_series = df.groupby("hour")["amount_ml"].sum()
        hourly_breakdown = {int(k): round(float(v), 1) for k, v in hourly_series.items()}

        return {
            "daily_average_ml": daily_average_ml,
            "current_streak_days": current_streak,
            "longest_streak_days": longest_streak,
            "hourly_breakdown": hourly_breakdown,
        }

    @staticmethod
    def get_weekly_trend(db: Session, user_id: int) -> Dict[str, float]:
        """Calculates 7-day water consumption trend with zero-fill for days without logs."""
        logs = WaterLogRepository.get_all_by_user(db, user_id)
        today = date.today()
        last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]

        if not logs:
            return {str(d): 0.0 for d in last_7_days}

        df = pd.DataFrame(
            [{"amount_ml": l.amount_ml, "logged_at": l.logged_at} for l in logs]
        )
        df["date"] = pd.to_datetime(df["logged_at"]).dt.date
        daily_totals = df.groupby("date")["amount_ml"].sum().to_dict()

        return {str(d): float(daily_totals.get(d, 0.0)) for d in last_7_days}
