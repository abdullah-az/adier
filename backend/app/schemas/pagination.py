from __future__ import annotations

from typing import Generic, Sequence, TypeVar

from pydantic.generics import GenericModel


T = TypeVar("T")


class PaginatedResponse(GenericModel, Generic[T]):
    """Standard response model for paginated endpoints."""

    items: Sequence[T]
    total: int
    offset: int
    limit: int


__all__ = ["PaginatedResponse"]
