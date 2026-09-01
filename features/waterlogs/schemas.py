"""Pydantic schemas for water logs."""

from datetime import datetime, timedelta, timezone
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


from enum import Enum


class QuickPresetEnum(str, Enum):
    GLASS_250 = "glass_250"
    MUG_350 = "mug_350"
    BOTTLE_500 = "bottle_500"
    FLASK_750 = "flask_750"
    BOTTLE_1000 = "bottle_1000"


PRESET_AMOUNTS: dict[QuickPresetEnum, float] = {
    QuickPresetEnum.GLASS_250: 250.0,
    QuickPresetEnum.MUG_350: 350.0,
    QuickPresetEnum.BOTTLE_500: 500.0,
    QuickPresetEnum.FLASK_750: 750.0,
    QuickPresetEnum.BOTTLE_1000: 1000.0,
}


class QuickLogCreate(BaseModel):
    preset: QuickPresetEnum = Field(
        default=QuickPresetEnum.GLASS_250,
        description="Preset beverage container size",
    )


class WaterLogCreate(BaseModel):
    amount_ml: float = Field(
        ...,
        gt=0.0,
        le=5000.0,
        description="Water intake amount in milliliters (max 5000ml per entry)",
    )
    logged_at: Optional[datetime] = Field(
        default=None,
        description="Optional custom consumption timestamp. Defaults to current UTC time.",
    )

    @field_validator("amount_ml")
    @classmethod
    def round_amount(cls, v: float) -> float:
        return round(v, 1)

    @field_validator("logged_at")
    @classmethod
    def validate_timestamp(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None:
            now_utc = datetime.now(timezone.utc)
            v_utc = v if v.tzinfo else v.replace(tzinfo=timezone.utc)
            if v_utc > now_utc + timedelta(minutes=5):
                raise ValueError("logged_at timestamp cannot be in the future")
        return v


class WaterLogUpdate(BaseModel):
    amount_ml: float = Field(..., gt=0, le=5000)

    @field_validator("amount_ml")
    @classmethod
    def round_amount(cls, v: float) -> float:
        return round(v, 1)


class WaterLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount_ml: float
    logged_at: datetime


class TodaySummary(BaseModel):
    total_ml: float
    goal_ml: float
    remaining_ml: float
    percent_complete: float
