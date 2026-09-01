import os
from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SQLITE_PATH = BASE_DIR / "watertrack.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    PROJECT_NAME: str = "WaterTrack API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security & JWT
    SECRET_KEY: str = "CHANGE_THIS_TO_A_RANDOM_SECRET_KEY_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database
    DATABASE_URL: str = f"sqlite:///{DEFAULT_SQLITE_PATH}"

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def resolve_database_url(cls, v: str) -> str:
        """Ensure relative SQLite database paths resolve to canonical project root and handle Render postgres URL."""
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql://", 1)
        if v.startswith("sqlite:///") and not v.startswith("sqlite:////") and not v.startswith("sqlite:///:memory:"):
            rel_path = v.replace("sqlite:///", "", 1).lstrip("./")
            abs_path = (BASE_DIR / rel_path).resolve()
            return f"sqlite:///{abs_path}"
        return v

    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["*"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    # External APIs
    OPEN_METEO_BASE_URL: str = "https://api.open-meteo.com/v1/forecast"
    OPEN_METEO_TIMEOUT_SECONDS: float = 5.0
    DEFAULT_ROOM_TEMP_CELSIUS: float = 22.0

    # Hydration Algorithm Constants
    BASE_ML_PER_KG: float = 35.0
    MIN_SAFE_FACTOR: float = 25.0
    MAX_SAFE_FACTOR: float = 55.0
    MIN_SAFE_FLOOR_ML: float = 1200.0
    MAX_SAFE_CEILING_ML: float = 6000.0


settings = Settings()
