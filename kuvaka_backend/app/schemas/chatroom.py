from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: int
    user_id: int
    gemini_response: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True

class ChatroomBase(BaseModel):
    name: str

class ChatroomCreate(ChatroomBase):
    pass

class ChatroomResponse(ChatroomBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        orm_mode = True
