"""User repository data access layer."""

from typing import Optional
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
        """Fetch user by email address."""
        return db.query(User).filter(User.email == email).first()

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
