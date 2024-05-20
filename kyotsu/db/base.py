__all__ = [
    "Base",
]

from typing import Self

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

from .mixins import TableNameMixin


class Base(AsyncAttrs, TableNameMixin, DeclarativeBase):
    def __repr__(self: Self) -> str:
        column_repr = (f"{c.key}={getattr(self, c.key)!r}" for c in self.__table__.columns)
        return f"{self.__class__.__name__}({", ".join(column_repr)})"
