import os
import sys
import types
from pathlib import Path

# Ensure current directory and parent are in sys.path
_CURRENT_DIR = Path(__file__).resolve().parent
if str(_CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(_CURRENT_DIR))

_PROJECT_ROOT = str(_CURRENT_DIR.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.append(_PROJECT_ROOT)

# Ensure 'app' package namespace resolves cleanly when running from repository root (Render / Docker)
if "app" not in sys.modules:
    _app_pkg = types.ModuleType("app")
    _app_pkg.__path__ = [str(_CURRENT_DIR)]
    _app_pkg.__file__ = str(_CURRENT_DIR / "__init__.py")
    sys.modules["app"] = _app_pkg

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.base import Base
from app.db.session import engine
import app.features.users.models  # noqa: F401
import app.features.waterlogs.models  # noqa: F401
import app.features.goals.models  # noqa: F401
import app.features.reminders.models  # noqa: F401



def create_app() -> FastAPI:
    """FastAPI Application Factory."""
    setup_logging()

    # Ensure tables are initialized
    Base.metadata.create_all(bind=engine)

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=(
            [settings.CORS_ORIGINS]
            if isinstance(settings.CORS_ORIGINS, str)
            else settings.CORS_ORIGINS
        ),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Standardized validation error handler
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = []
        for err in exc.errors():
            loc = [
                str(x)
                for x in err.get("loc", [])
                if x not in ("body", "query")
            ]
            field_name = ".".join(loc) if loc else "general"
            raw_msg = err.get("msg", "Invalid input")
            if raw_msg.startswith("Value error, "):
                raw_msg = raw_msg.replace("Value error, ", "", 1)
            errors.append({"field": field_name, "message": raw_msg})

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "message": "Validation failed on one or more fields.",
                "errors": errors,
            },
        )

    # Health check / status endpoint
    @app.get("/", status_code=status.HTTP_200_OK, tags=["General"])
    def read_root() -> dict[str, str]:
        return {"message": "WaterTrack API is running"}

    # Include routes both at root level (backwards-compatible) and under /api/v1
    app.include_router(api_router)
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_app()
