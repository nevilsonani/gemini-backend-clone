from pathlib import Path
from dotenv import load_dotenv
import os

# Always load .env from Kuvaka Task/.env (project root)
env_path = Path(__file__).resolve().parents[3] / ".env"
# Load .env from project root for Celery/gemini context
load_dotenv(dotenv_path=env_path)


# Force import all models to ensure SQLAlchemy relationships are registered
from app.models import chatroom, message, user

import asyncio
import logging
from app.core.celery_app import celery_app
import asyncio
import os
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.future import select
from app.models.message import Message

DATABASE_URL = os.getenv("DATABASE_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

async def call_gemini_api(user_message: str, api_key: str) -> str:
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": user_message}]}
        ]
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(GEMINI_API_URL, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        # Debug: log full Gemini API response
                # Try to extract the text response robustly
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as parse_exc:
                        return str(data)  # Save raw response if parsing fails

import logging

@celery_app.task
def process_gemini_message(message_id: int, user_message: str):
    async def do_work():
        try:
            # Call Gemini API
            try:
                gemini_response = await call_gemini_api(user_message, GEMINI_API_KEY)
            except Exception as e:
                logging.exception("Error calling Gemini API")
                gemini_response = f"[Gemini API Error] {str(e)}"

            # Update the message in DB
            try:
                engine = create_async_engine(DATABASE_URL, echo=False)
                async with AsyncSession(engine) as session:
                    result = await session.execute(select(Message).where(Message.id == message_id))
                    message = result.scalar_one_or_none()
                    if message:
                        message.gemini_response = gemini_response
                        await session.commit()
                await engine.dispose()
            except Exception as db_exc:
                logging.exception("Error updating Gemini response in DB")
                return f"DB Error: {db_exc}"
            return True
        except Exception as exc:
            logging.exception("process_gemini_message failed")
            return f"Task Error: {exc}"
    try:
        return asyncio.run(do_work())
    except Exception as exc:
        logging.exception("asyncio.run failed in process_gemini_message")
        return f"asyncio.run Error: {exc}"

