"""Error handling: structured exceptions, responses, and helper functions."""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Application-level error with structured code and message."""

    def __init__(self, code: str, message: str, status_code: int = 400, details: Any = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


class NotFoundError(AppError):
    def __init__(self, entity: str, entity_id: str):
        super().__init__(
            code=f"{entity.upper()}_NOT_FOUND",
            message=f"{entity} with ID {entity_id} not found",
            status_code=404,
        )


class DuplicateError(AppError):
    def __init__(self, entity: str, field: str, value: str):
        super().__init__(
            code=f"{entity.upper()}_DUPLICATE",
            message=f"{entity} with {field} '{value}' already exists",
            status_code=409,
        )


class RateLimitError(AppError):
    def __init__(self, source: str, retry_after: int = 60):
        super().__init__(
            code="RATE_LIMIT_EXCEEDED",
            message=f"Rate limit exceeded for {source}. Retry after {retry_after}s",
            status_code=429,
            details={"retry_after_seconds": retry_after},
        )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        },
    )


def success_response(data: Any = None, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    resp: Dict[str, Any] = {"status": "success", "data": data}
    if meta:
        resp["meta"] = meta
    return resp


def pagination_meta(page: int, limit: int, total: int, execution_ms: int = 0) -> Dict[str, Any]:
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "execution_ms": execution_ms,
    }