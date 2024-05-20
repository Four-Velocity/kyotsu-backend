from collections.abc import AsyncIterator

from kyotsu.config import get_settings
from kyotsu.db.sessionmaker import AsyncSessionMaker
from sqlalchemy.ext.asyncio import AsyncSession

sessionmaker = AsyncSessionMaker(get_settings().POSTGRES)


async def d_session() -> AsyncIterator[AsyncSession]:
    try:
        db = sessionmaker()
        yield db
    finally:
        await db.close()
