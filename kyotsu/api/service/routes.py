from typing import Annotated

from pydantic import BaseModel, ConfigDict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from kyotsu.api.dependencies import d_session
from kyotsu.db import EventCodeSeverityEnum
from kyotsu.db.models import EventCode
from kyotsu.utis import parse_error_code, get_prefix_ids_by_composed_key_query

router = APIRouter()


class EventCodeR(BaseModel):
    code: str
    details: str
    hint: str | None
    severity: EventCodeSeverityEnum


@router.get("/event_code/{code}")
async def get_error_code_details(code: str, db: Annotated[AsyncSession, Depends(d_session)]):
    prefixes, increment = parse_error_code(code.upper())
    query = get_prefix_ids_by_composed_key_query(prefixes)
    prefix_id = (await db.execute(query)).fetchone()[0]
    if not prefix_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"details": f"Prefix '{".".join(prefixes)}' is not found."})
    event_code_query = select(EventCode).where((EventCode.prefix_id == prefix_id) & (EventCode.increment == increment))

    try:
        event_code = (await db.execute(event_code_query)).scalars().unique().one()
    except NoResultFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"details": f"EventCode '{code}' is not found."}) from e
    if event_code.use_generic_message:
        message = "Something went wrong."
    else:
        message = event_code.custom_message
    return EventCodeR(
        code=code,
        details=message,
        hint=event_code.hint,
        severity=event_code.severity
    )
