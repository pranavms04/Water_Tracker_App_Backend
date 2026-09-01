"""Authentication router."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.features.auth.schemas import LoginResponse, UserLogin
from app.features.auth.service import AuthService
from app.features.users.models import User
from app.features.users.schemas import UserCreate, UserProfileResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register_user(
    user_in: UserCreate, db: Session = Depends(get_db)
) -> User:
    return AuthService.register_user(db, user_in)


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and retrieve access token",
)
def login_user(
    credentials: UserLogin, db: Session = Depends(get_db)
) -> LoginResponse:
    return AuthService.authenticate_user(db, credentials)


@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get profile of the currently authenticated user",
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user
