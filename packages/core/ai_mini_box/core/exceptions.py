class AppError(Exception):
    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        self.exit_code = exit_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, entity: str, id: int):
        super().__init__(f"{entity} with id {id} not found", exit_code=2)


class ConfigError(AppError):
    def __init__(self, message: str):
        super().__init__(message, exit_code=3)
