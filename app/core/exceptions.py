from fastapi import status


class AppError(Exception):
    """Base class for domain errors mapped to HTTP responses by the handlers in main.py."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_message: str = "Internal server error"

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class UserAlreadyExistsError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_message = "User already exists"


class InvalidCredentialsError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_message = "Invalid credentials"
