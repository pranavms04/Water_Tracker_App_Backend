"""Machine learning module for WaterTrack."""

from app.features.ml.router import router
from app.features.ml.service import MLService

__all__ = ["router", "MLService"]
