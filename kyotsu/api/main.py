import dataclasses
from typing import Any

from fastapi import FastAPI
from starlette.requests import Request
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin import StringField, EnumField
from .dependencies import sessionmaker
from kyotsu.db import EventCode, Prefix, EventCodeSeverityEnum
from kyotsu.api.service.routes import router as service_router

app = FastAPI()
app.include_router(service_router)

admin = Admin(sessionmaker._engine, title="Error DB")


class PrefixView(ModelView):
    row_actions = ["view", "edit"]
    actions = []
    fields = [
        Prefix.id,
        Prefix.prefix,
        Prefix.alias,
        Prefix.description,
        Prefix.parent_prefix,
        Prefix.child_prefixes,
        Prefix.event_codes,
        Prefix.created_at,
        Prefix.updated_at,
    ]
    exclude_fields_from_list = [
        Prefix.description,
        Prefix.child_prefixes,
        Prefix.event_codes,
        Prefix.created_at,
    ]
    exclude_fields_from_create = [
        Prefix.event_codes,
        Prefix.child_prefixes,
        Prefix.created_at,
        Prefix.updated_at,
    ]
    exclude_fields_from_edit = [
        Prefix.child_prefixes,
        Prefix.event_codes,
        Prefix.created_at,
        Prefix.updated_at,
    ]


@dataclasses.dataclass
class AStringField(StringField):
    read_only = True

    async def parse_obj(self, request: Request, obj: Any) -> Any:
        coro = await super().parse_obj(request, obj)
        return await coro


@dataclasses.dataclass
class ShortUUIDField(StringField):
    read_only = True

    async def parse_obj(self, request: Request, obj: Any) -> Any:
        val = str(await super().parse_obj(request, obj))
        return f"{val[:9]}...{val[-9:]}"


class EventCodeView(ModelView):
    row_actions = ["view", "edit"]
    actions = []
    fields = [
        EventCode.id,
        AStringField("str_value", label="Event Code", read_only=True),
        EventCode.custom_message,
        EventCode.severity,
        EventCode.dev_note,
        EventCode.is_deprecated,
        EventCode.use_generic_message,
        EventCode.is_private,
        EventCode.prefix,
        EventCode.hint,
        EventCode.created_at,
        EventCode.updated_at,
    ]

    exclude_fields_from_list = [
        EventCode.custom_message,
        EventCode.dev_note,
        EventCode.use_generic_message,
        EventCode.hint,
        EventCode.created_at,
    ]

    exclude_fields_from_edit = [
        "id",
        "str_value",
        EventCode.created_at,
        EventCode.updated_at,
        EventCode.prefix,
    ]

    exclude_fields_from_create = [
        "id",
        "str_value",
        EventCode.created_at,
        EventCode.updated_at,
        EventCode.is_deprecated,
    ]

admin.add_view(PrefixView(Prefix, label="Prefixes", icon="fas fa-tags"))
icon = "fas fa-tag"
admin.add_view(EventCodeView(EventCode, label="Event Codes", icon="fas fa-eye"))

admin.mount_to(app)
