__all__ = [
    "AsyncSessionMaker",
    "SessionMaker",
]

import abc
from typing import Any, Generic, Self, TypeVar

from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from kyotsu.config import PostgresConnection

TEngine = TypeVar("TEngine", Engine, AsyncEngine)
TSession = TypeVar("TSession", Session, AsyncSession)


class AbstractSessionMaker(abc.ABC, Generic[TEngine, TSession]):
    ENGINE: str

    def __init__(
        self: Self,
        conn_settings: PostgresConnection,
        *,
        rebind_new_engine: bool = False,
        new_engine_kwargs: dict[str, Any] | None = None,
        **session_maker_kwargs: Any,
    ):
        self._new_engine_kwargs = new_engine_kwargs or {}
        self._conn_str = conn_settings.CONN_STR.replace("postgresql", f"postgresql+{self.ENGINE}")
        self._rebind_new_engine = rebind_new_engine
        self._session_maker_kwargs = session_maker_kwargs
        self._engine: TEngine | None = self.get_new_engine() if not self._rebind_new_engine else None

    @abc.abstractmethod
    def __call__(self: Self) -> TSession: ...

    @abc.abstractmethod
    def get_new_engine(self: Self) -> TEngine: ...


class SessionMaker(AbstractSessionMaker[Engine, Session]):
    ENGINE = "psycopg2"

    def __call__(self: Self) -> Session:
        engine = self._engine if self._engine is not None else self.get_new_engine()
        session: Session = sessionmaker(bind=engine, **self._session_maker_kwargs)()
        return session

    def get_new_engine(self: Self) -> Engine:
        engine: Engine = create_engine(self._conn_str, **self._new_engine_kwargs)
        return engine


class AsyncSessionMaker(AbstractSessionMaker[AsyncEngine, AsyncSession]):
    ENGINE = "asyncpg"

    def __call__(self: Self) -> AsyncSession:
        engine = self._engine if self._engine is not None else self.get_new_engine()
        session: AsyncSession = async_sessionmaker(bind=engine, **self._session_maker_kwargs)()
        return session

    def get_new_engine(self: Self) -> AsyncEngine:
        engine: AsyncEngine = create_async_engine(self._conn_str, **self._new_engine_kwargs)
        return engine
