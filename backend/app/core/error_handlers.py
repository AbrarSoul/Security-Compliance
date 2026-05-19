"""Centralized API error responses for consistent client handling."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, list):
            message = detail
        elif isinstance(detail, dict):
            message = detail.get("message", detail)
        else:
            message = detail
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": message,
                "error": {
                    "code": exc.status_code,
                    "message": message,
                    "type": "http_error",
                },
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = exc.errors()
        return JSONResponse(
            status_code=422,
            content={
                "detail": errors,
                "error": {
                    "code": 422,
                    "message": "Request validation failed",
                    "type": "validation_error",
                    "details": errors,
                },
            },
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(
        _request: Request, exc: ValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": 422,
                    "message": "Invalid request data",
                    "type": "validation_error",
                    "details": exc.errors(),
                }
            },
        )
