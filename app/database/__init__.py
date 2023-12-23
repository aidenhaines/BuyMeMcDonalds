from beanie import init_beanie as _init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from app.database.models import __beanie_models__


async def init_beanie(
    host: str, database: str, port: int = 27017, user: str = None, password: str = None
) -> None:
    client = AsyncIOMotorClient(username=user, password=password, host=host, port=port)
    await _init_beanie(database=client[database], document_models=__beanie_models__)
