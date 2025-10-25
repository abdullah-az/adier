from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field
from pydantic.generics import GenericModel


DataT = TypeVar("DataT")


class ResponseStatus(BaseModel):
    """Represents the status metadata returned for every API response."""

    code: str = Field(default="OK", description="Application-specific status code")
    message: str = Field(default="Success", description="Human readable status message")


class PaginationMeta(BaseModel):
    """Metadata describing the pagination context for list responses."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=200)
    total_items: int = Field(default=0, ge=0)
    total_pages: int = Field(default=0, ge=0)
    sort_by: Optional[str] = Field(default=None)
    sort_order: Optional[str] = Field(default=None)
    locale: Optional[str] = Field(default=None)


class ApiResponse(GenericModel, Generic[DataT]):
    """Envelope returned by the API for non-paginated responses."""

    status: ResponseStatus
    data: Optional[DataT] = Field(default=None)
    meta: Optional[dict[str, Any]] = Field(default=None)


class PaginatedResponse(GenericModel, Generic[DataT]):
    """Envelope returned by the API for paginated list responses."""

    status: ResponseStatus
    data: list[DataT] = Field(default_factory=list)
    meta: PaginationMeta


class ErrorDetail(BaseModel):
    """Describes an individual validation or processing error."""

    code: str = Field(default="ERROR", description="Machine-readable error code")
    message: str = Field(..., description="Human readable error message")
    field: Optional[str] = Field(default=None, description="Optional field path related to the error")


class ErrorResponse(BaseModel):
    """Standardised error response payload."""

    status: ResponseStatus
    errors: list[ErrorDetail] = Field(default_factory=list)
    data: Optional[Any] = Field(default=None)


__all__ = [
    "ApiResponse",
    "PaginatedResponse",
    "PaginationMeta",
    "ResponseStatus",
    "ErrorResponse",
    "ErrorDetail",
]
