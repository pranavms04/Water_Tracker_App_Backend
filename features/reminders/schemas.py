"""Pydantic schemas for reminder settings."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReminderSettingsUpdate(BaseModel):
    enabled: bool
    interval_minutes: int = Field(..., ge=15, le=480)
    start_time: str = Field(..., pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    end_time: str = Field(..., pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")

    @field_validator("end_time")
    @classmethod
    def end_after_start(cls, v: str, info) -> str:
        start = info.data.get("start_time")
        if start and v <= start:
            raise ValueError("end_time must be after start_time")
        return v


class ReminderSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    enabled: bool
    interval_minutes: int
    start_time: str
    end_time: str
