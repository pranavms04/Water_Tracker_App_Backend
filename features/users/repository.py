"""User repository data access layer."""

from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.features.users.models import User


class UserRepository:
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        """Fetch user by internal integer ID."""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_by_uuid(db: Session, user_uuid: str) -> Optional[User]:
        """Fetch user by public UUID string."""
        return db.query(User).filter(User.user_uuid == user_uuid).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """Fetch user by email address (case-insensitive and trimmed)."""
        if not email:
            return None
        normalized = email.strip().lower()
        return (
            db.query(User)
            .filter(func.lower(User.email) == normalized)
            .first()
        )

    @staticmethod
    def create(db: Session, user: User) -> User:
        """Add new user to database."""
        db.add(user)
        return user

    @staticmethod
    def update(db: Session, user: User) -> User:
        """Commit changes to an existing user."""
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
