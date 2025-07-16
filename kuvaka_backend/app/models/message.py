from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.user import Base
# Do NOT import Chatroom here; use string references in relationships only.

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    chatroom_id = Column(Integer, ForeignKey("chatrooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    gemini_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    chatroom = relationship("Chatroom", back_populates="messages")
