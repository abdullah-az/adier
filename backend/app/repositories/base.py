from __future__ import annotations

from typing import Any, Dict, Generic, Iterable, Optional, Type, TypeVar

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.base import Base


ModelType = TypeVar("ModelType", bound=Base)


class SQLAlchemyRepository(Generic[ModelType]):
    """Generic repository implementing common CRUD helpers."""

    model_cls: Type[ModelType]

    def __init__(self, session: Session) -> None:
        if not hasattr(self, "model_cls"):
            raise ValueError("Repository must define a model_cls attribute")
        self.session = session

    def get(self, entity_id: str) -> Optional[ModelType]:
        return self.session.get(self.model_cls, entity_id)

    def list(self, *, offset: int = 0, limit: int = 100) -> Iterable[ModelType]:
        stmt = select(self.model_cls).offset(offset).limit(limit)
        return self.session.execute(stmt).scalars().all()

    def create(self, obj_in: BaseModel | Dict[str, Any]) -> ModelType:
        data = self._to_data(obj_in)
        instance = self.model_cls(**data)
        self.session.add(instance)
        self.session.commit()
        self.session.refresh(instance)
        return instance

    def update(self, instance: ModelType, obj_in: BaseModel | Dict[str, Any]) -> ModelType:
        data = self._to_data(obj_in, exclude_unset=True)
        for field, value in data.items():
            setattr(instance, field, value)
        self.session.add(instance)
        self.session.commit()
        self.session.refresh(instance)
        return instance

    def delete(self, instance: ModelType) -> None:
        self.session.delete(instance)
        self.session.commit()

    @staticmethod
    def _to_data(obj_in: BaseModel | Dict[str, Any], *, exclude_unset: bool = False) -> Dict[str, Any]:
        if isinstance(obj_in, BaseModel):
            return obj_in.model_dump(exclude_unset=exclude_unset)
        return obj_in


__all__ = ["SQLAlchemyRepository"]
