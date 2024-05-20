__all__ = [
    "TableNameMixin",
    "TimeLoggedMixinDDL",
    "UUIDMixin",
    "get_onupdate_function",
    "get_table_trigger",
]

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Self

import inflection
from sqlalchemy import DateTime, FetchedValue, func, text
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

if TYPE_CHECKING:
    from alembic_utils.pg_function import PGFunction  # type: ignore[import-untyped]
    from alembic_utils.pg_trigger import PGTrigger  # type: ignore[import-untyped]


class TableNameMixin:
    @declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        return inflection.pluralize(inflection.underscore(cls.__name__))


class TimeLoggedMixinDDL:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp of creation",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        server_onupdate=FetchedValue(),
        nullable=False,
        comment="Timestamp of last update",
    )


def get_onupdate_function(schema: str = "public", column: str = "updated_at") -> "PGFunction":
    from alembic_utils.pg_function import PGFunction

    return PGFunction(
        schema=schema,
        signature=f"update_{column}_column()",
        definition=(
            f"RETURNS TRIGGER AS $$ "
            f"BEGIN "
            f"    NEW.{column} = now(); "
            f"    RETURN NEW; "
            f"END; "
            f"$$ language 'plpgsql';"
        ),
    )


def get_table_trigger(tablename: str, schema: str = "public", column: str = "updated_at") -> "PGTrigger":
    from alembic_utils.pg_trigger import PGTrigger

    return PGTrigger(
        schema=schema,
        signature=f"trg_{tablename}__{column}_auto",
        on_entity=f"{schema}.{tablename}",
        is_constraint=False,
        definition=(
            f"    BEFORE UPDATE "
            f"    ON {tablename} "
            f"    FOR EACH ROW "
            f"EXECUTE FUNCTION "
            f"    update_{column}_column();"
        ),
    )


class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        comment="Unique UUID identifier",
    )

    def __str__(self: Self) -> str:
        return f"{self.__class__.__name__} ({self.id})"
