"""Custom domain and HTTP exceptions."""

from typing import Any, Optional
from fastapi import HTTPException, status


class DomainException(Exception):
    """Base domain exception."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ResourceNotFoundException(HTTPException):
    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ResourceAlreadyExistsException(HTTPException):
    def __init__(self, detail: str = "Resource already exists") -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class UnauthorizedException(HTTPException):
    def __init__(self, detail: str = "Could not validate credentials") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenException(HTTPException):
    def __init__(
        self, detail: str = "You are not authorized to perform this action"
    ) -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ValidationException(HTTPException):
    def __init__(self, detail: str = "Validation failed") -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail
        )


class DatabaseException(HTTPException):
    def __init__(self, detail: str = "A database error occurred") -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail
        )
