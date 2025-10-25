from __future__ import annotations

import math
from typing import Any, Iterable, Optional, Sequence

from fastapi.responses import JSONResponse

from app.schemas.common import ApiResponse, PaginatedResponse, PaginationMeta, ResponseStatus


def success_response(
    data: Any = None,
    *,
    message: str = "Request completed successfully",
    code: str = "OK",
    meta: Optional[dict[str, Any]] = None,
) -> ApiResponse[Any]:
    """Produce a standardised success response envelope."""

    status = ResponseStatus(code=code, message=message)
    return ApiResponse[Any](status=status, data=data, meta=meta)


def paginated_response(
    items: Sequence[Any],
    *,
    page: int,
    page_size: int,
    total_items: int,
    message: str = "Request completed successfully",
    code: str = "OK",
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    locale: Optional[str] = None,
    extra_meta: Optional[dict[str, Any]] = None,
) -> PaginatedResponse[Any]:
    """Produce a paginated response envelope with derived metadata."""

    total_pages = math.ceil(total_items / page_size) if page_size else 0
    meta = PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
        sort_by=sort_by,
        sort_order=sort_order,
        locale=locale,
    ).model_dump()
    if extra_meta:
        meta.update(extra_meta)
    status = ResponseStatus(code=code, message=message)
    return PaginatedResponse[Any](status=status, data=list(items), meta=meta)


def empty_response(*, message: str = "Request completed successfully", code: str = "OK") -> ApiResponse[None]:
    """Produce a response envelope without payload."""

    status = ResponseStatus(code=code, message=message)
    return ApiResponse[None](status=status, data=None)


def error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    errors: Optional[list[dict[str, Any]]] = None,
    data: Any = None,
) -> JSONResponse:
    """Produce a JSON response containing a standardised error envelope."""

    payload: dict[str, Any] = {
        "status": ResponseStatus(code=code, message=message).model_dump(),
    }
    if errors:
        payload["errors"] = errors
    if data is not None:
        payload["data"] = data
    return JSONResponse(status_code=status_code, content=payload)
