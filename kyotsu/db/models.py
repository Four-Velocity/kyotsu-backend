import uuid
import datetime
from typing import Any, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Time
from sqlalchemy.dialects.postgresql import ARRAY, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kyotsu.db.base import Base
from kyotsu.db.constants import EventCodeSeverityEnum
from kyotsu.db.mixins import UUIDMixin, TimeLoggedMixinDDL as TimeLoggedMixin

if TYPE_CHECKING:
    from fastapi import Request


class Prefix(TimeLoggedMixin, Base):
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    prefix: Mapped[str] = mapped_column(nullable=False)
    alias: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    parent_prefix_id: Mapped[int] = mapped_column(
        ForeignKey("prefixes.id", onupdate="CASCADE", ondelete="CASCADE"),
        unique=False,
        nullable=True
    )

    parent_prefix: Mapped["Prefix"] = relationship(back_populates="child_prefixes", remote_side=[id])
    child_prefixes: Mapped[list["Prefix"]] = relationship(back_populates="parent_prefix")
    event_codes: Mapped[list["EventCode"]] = relationship(back_populates="prefix")

    @property
    async def str_value(self):
        if not self.parent_prefix_id:
            return self.prefix
        else:
            await self.awaitable_attrs.parent_prefix
            return (await self.parent_prefix.str_value) + "." + self.prefix

    async def __admin_repr__(self, _: "Request") -> str:
        return await self.str_value

    async def __admin_select2_repr__(self, _: "Request"):
        text = await self.str_value
        html = (
            f"<span>"
            f"{self.id} :: {text} :: {self.alias}"
            f"</span>"
        )
        return html


class EventCode(UUIDMixin, TimeLoggedMixin, Base):
    prefix_id: Mapped[int] = mapped_column(
        ForeignKey("prefixes.id", onupdate="CASCADE", ondelete="CASCADE"),
        unique=False,
        nullable=False,
    )
    increment: Mapped[int] = mapped_column(unique=False, nullable=False, default=0)

    custom_message: Mapped[str] = mapped_column(nullable=True)
    hint: Mapped[str] = mapped_column(nullable=True)
    severity: Mapped[EventCodeSeverityEnum] = mapped_column(nullable=False, unique=False)
    dev_note: Mapped[str] = mapped_column(nullable=True)

    is_deprecated: Mapped[bool] = mapped_column(
        nullable=False,
        server_default="f",
        default=False,
    )
    use_generic_message: Mapped[bool] = mapped_column(
        nullable=False,
        server_default="f",
        default=False,
    )
    is_private: Mapped[bool] = mapped_column(
        nullable=False,
        server_default="f",
        default=False,
    )

    prefix: Mapped["Prefix"] = relationship(back_populates="event_codes")

    @property
    async def str_value(self):
        await self.awaitable_attrs.prefix
        return f"{(await self.prefix.str_value)}{self.increment:0>4}"

    async def __admin_repr__(self, _: "Request"):
        return await self.str_value

    async def __admin_select2_repr__(self, _: "Request"):
        text = await self.str_value
        return f"<span>{text}</span>"
