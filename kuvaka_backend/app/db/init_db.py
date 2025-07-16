import os
from dotenv import load_dotenv
import asyncio

# Always load .env from project root (Kuvaka Task/.env)
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))
load_dotenv(dotenv_path=env_path)

from app.db.session import engine
from app.models.user import Base
from app.models.chatroom import Chatroom
from app.models.message import Message

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
if __name__ == "__main__":
    asyncio.run(init_db())
