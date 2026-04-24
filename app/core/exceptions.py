class AppError(Exception):
    pass


class UserAlreadyExistsError(AppError):
    pass


class InvalidCredentialsError(AppError):
    pass
