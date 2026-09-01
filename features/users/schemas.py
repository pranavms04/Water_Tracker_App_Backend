"""Pydantic schemas for user domain."""

from datetime import datetime
from enum import Enum
from typing import Optional
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
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    weight_kg: Optional[float] = Field(default=None, gt=20.0, le=300.0)
    gender: Optional[GenderEnum] = GenderEnum.OTHER
    activity_level: Optional[ActivityLevelEnum] = ActivityLevelEnum.MODERATE


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=72)
    daily_goal_ml: Optional[float] = Field(default=None, ge=500, le=10000)

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Full name cannot be blank or whitespace only")
        return cleaned


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
