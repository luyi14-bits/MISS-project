from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey
from datetime import datetime, timezone

from models import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    role = Column(String)
    content = Column(Text)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
