"""Pydantic schemas for user domain."""

from datetime import datetime
from enum import Enum
import math
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class GenderEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class ActivityLevelEnum(str, Enum):
    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    VERY_ACTIVE = "very_active"


class UserBase(BaseModel):
    email: EmailStr = Field(..., max_length=254)
    full_name: str = Field(..., min_length=1, max_length=100)
    weight_kg: Optional[float] = Field(default=None, gt=20.0, le=300.0)
    gender: Optional[GenderEnum] = GenderEnum.OTHER
    activity_level: Optional[ActivityLevelEnum] = ActivityLevelEnum.MODERATE

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: Any) -> Any:
        if isinstance(v, str):
            v = v.strip().lower()
            if not v:
                raise ValueError("Email cannot be blank or whitespace only")
        return v

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Full name cannot be blank or whitespace only")
        return cleaned

    @field_validator("weight_kg")
    @classmethod
    def validate_weight(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if math.isnan(v) or math.isinf(v):
                raise ValueError("Weight must be a valid finite number")
        return v


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=72)
    daily_goal_ml: Optional[float] = Field(default=None, ge=500, le=10000)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if "\x00" in v:
            raise ValueError("Password cannot contain null characters")
        if not v.strip():
            raise ValueError("Password cannot be blank or whitespace only")
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password cannot exceed 72 bytes")
        has_letter = any(c.isalpha() for c in v)
        has_digit = any(c.isdigit() for c in v)
        if not has_letter or not has_digit:
            raise ValueError(
                "Password must contain at least one letter and one number"
            )
        return v

    @field_validator("daily_goal_ml")
    @classmethod
    def validate_daily_goal(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if math.isnan(v) or math.isinf(v):
                raise ValueError("Daily goal must be a valid finite number")
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    weight_kg: Optional[float] = Field(default=None, gt=20.0, le=300.0)
    gender: Optional[GenderEnum] = None
    activity_level: Optional[ActivityLevelEnum] = None

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Full name cannot be blank or whitespace only")
            return cleaned
        return v

    @field_validator("weight_kg")
    @classmethod
    def validate_weight(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if math.isnan(v) or math.isinf(v):
                raise ValueError("Weight must be a valid finite number")
        return v


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str = Field(validation_alias="user_uuid")
    email: EmailStr
    full_name: str
    weight_kg: Optional[float] = None
    gender: Optional[str] = None
    activity_level: Optional[str] = None
    created_at: datetime


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str = Field(validation_alias="user_uuid")
    email: EmailStr
    full_name: str
    weight_kg: Optional[float] = None
    gender: Optional[str] = None
    activity_level: Optional[str] = None
    created_at: datetime
