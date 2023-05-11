import os

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from core.db.nosql.model import model_list


class Driver:
    def __init__(self):
        self.client = AsyncIOMotorClient(os.getenv("DB_URL"))

    async def connect(self):
        await init_beanie(database=self.client.bot_prod, document_models=model_list)
