from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import get_db
from app.models.chatroom import Chatroom
from app.models.message import Message
from app.models.user import User
from app.schemas.chatroom import ChatroomCreate, ChatroomResponse, MessageCreate, MessageResponse
from app.core import security
from typing import List
from datetime import datetime, timedelta

router = APIRouter()

# POST /chatroom - create a new chatroom
def get_current_user(token: str = Depends(security.oauth2_scheme), db: AsyncSession = Depends(get_db)):
    payload = security.verify_access_token(token)
    user_id = int(payload["sub"])
    return user_id

@router.post("/chatroom", response_model=ChatroomResponse)
async def create_chatroom(
    data: ChatroomCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    chatroom = Chatroom(user_id=user_id, name=data.name)
    db.add(chatroom)
    await db.commit()
    await db.refresh(chatroom)
    # Invalidate chatroom cache for this user
    cache_key = f"chatrooms:{user_id}"
    await redis_client.delete(cache_key)
    return ChatroomResponse(
        id=chatroom.id,
        user_id=chatroom.user_id,
        name=chatroom.name,
        created_at=chatroom.created_at,
        updated_at=chatroom.updated_at,
        messages=[]
    )

# GET /chatroom - list all chatrooms for user
from app.core.redis import redis_client
import json

@router.get("/chatroom", response_model=List[ChatroomResponse])
async def list_chatrooms(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    cache_key = f"chatrooms:{user_id}"
    cached = await redis_client.get(cache_key)
    if cached:
        return [ChatroomResponse(**item) for item in json.loads(cached)]
    result = await db.execute(select(Chatroom).where(Chatroom.user_id == user_id))
    chatrooms = result.scalars().all()
    from datetime import datetime
    def serialize_chatroom(chat):
        d = ChatroomResponse(
            id=chat.id,
            user_id=chat.user_id,
            name=chat.name,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            messages=[]
        ).dict()
        # Convert datetime fields to isoformat
        d['created_at'] = d['created_at'].isoformat() if isinstance(d['created_at'], datetime) else d['created_at']
        d['updated_at'] = d['updated_at'].isoformat() if isinstance(d['updated_at'], datetime) else d['updated_at']
        return d
    data = [serialize_chatroom(chat) for chat in chatrooms]
    await redis_client.set(cache_key, json.dumps(data), ex=30)
    return [ChatroomResponse(**item) for item in data]

# GET /chatroom/{id} - get chatroom details
@router.get("/chatroom/{id}", response_model=ChatroomResponse)
async def get_chatroom(
    id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    chatroom = await db.get(Chatroom, id)
    if not chatroom or chatroom.user_id != user_id:
        raise HTTPException(status_code=404, detail="Chatroom not found")
    return ChatroomResponse(
        id=chatroom.id,
        user_id=chatroom.user_id,
        name=chatroom.name,
        created_at=chatroom.created_at,
        updated_at=chatroom.updated_at,
        messages=[]
    )

# POST /chatroom/{id}/message - send message (Gemini async integration to be added)
from app.services.gemini import process_gemini_message

from sqlalchemy.future import select
from app.models.user import User

@router.post("/chatroom/{id}/message", response_model=MessageResponse)
async def send_message(
    id: int,
    data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    chatroom = await db.get(Chatroom, id)
    if not chatroom or chatroom.user_id != user_id:
        raise HTTPException(status_code=404, detail="Chatroom not found")
    # Rate limit for Basic users
    user = await db.get(User, user_id)
    if not user.is_pro:
        today = datetime.utcnow().date()
        tomorrow = today + timedelta(days=1)
        result = await db.execute(
            select(Message).where(
                Message.user_id == user_id,
                Message.created_at >= datetime.combine(today, datetime.min.time()),
                Message.created_at < datetime.combine(tomorrow, datetime.min.time())
            )
        )
        count_today = len(result.scalars().all())
        if count_today >= 10:
            raise HTTPException(status_code=429, detail="Daily message limit reached. Upgrade to Pro for unlimited access.")
    message = Message(chatroom_id=id, user_id=user_id, content=data.content, created_at=datetime.utcnow())
    db.add(message)
    await db.commit()
    await db.refresh(message)
    # Invalidate chatroom cache for this user
    cache_key = f"chatrooms:{user_id}"
    await redis_client.delete(cache_key)
    # Enqueue Gemini async task
    process_gemini_message.delay(message.id, data.content)
    return MessageResponse(
        id=message.id,
        user_id=message.user_id,
        content=message.content,
        gemini_response=message.gemini_response,
        created_at=message.created_at
    )

# GET /chatroom/{id}/messages - get all messages in a chatroom
@router.get("/chatroom/{id}/messages", response_model=List[MessageResponse])
async def get_chatroom_messages(
    id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    chatroom = await db.get(Chatroom, id)
    if not chatroom or chatroom.user_id != user_id:
        raise HTTPException(status_code=404, detail="Chatroom not found")
    result = await db.execute(select(Message).where(Message.chatroom_id == id))
    messages = result.scalars().all()
    return [
        MessageResponse(
            id=msg.id,
            user_id=msg.user_id,
            content=msg.content,
            gemini_response=msg.gemini_response,
            created_at=msg.created_at
        )
        for msg in messages
    ]

# GET /message/{id} - get a single message by ID
@router.get("/message/{id}", response_model=MessageResponse)
async def get_message(
    id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    result = await db.execute(select(Message).where(Message.id == id))
    message = result.scalar_one_or_none()
    if not message or message.user_id != user_id:
        raise HTTPException(status_code=404, detail="Message not found")
    return MessageResponse(
        id=message.id,
        user_id=message.user_id,
        content=message.content,
        gemini_response=message.gemini_response,
        created_at=message.created_at
    )
