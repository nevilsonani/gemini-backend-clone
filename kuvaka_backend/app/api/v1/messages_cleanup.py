from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import get_db
from app.models.message import Message
from app.core import security

router = APIRouter()

def get_current_user(token: str = Depends(security.oauth2_scheme), db: AsyncSession = Depends(get_db)):
    payload = security.verify_access_token(token)
    user_id = int(payload["sub"])
    return user_id

@router.delete("/messages/cleanup")
async def cleanup_messages(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    # Find messages with null or error gemini_response
    result = await db.execute(select(Message).where(
        Message.user_id == user_id,
        ((Message.gemini_response == None) |
         (Message.gemini_response.ilike('%[Gemini API Error]%')))
    ))
    messages = result.scalars().all()
    deleted_count = 0
    for msg in messages:
        await db.delete(msg)
        deleted_count += 1
    await db.commit()
    return {"deleted": deleted_count}
