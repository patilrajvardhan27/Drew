from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """An error whose message is safe to show to the user."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


class NotFound(AppError):
    def __init__(self, label: str):
        super().__init__(404, f"{label} not found")


def install_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status, content={"detail": exc.message})
