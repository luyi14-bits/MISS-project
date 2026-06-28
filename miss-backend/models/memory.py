from sqlalchemy import Column, String, DateTime, Integer, Text
from datetime import datetime, timezone

from models import Base

class MemoryEntry(Base):
    __tablename__ = "memory_entries"

    id = Column(String, primary_key=True)
    session_id = Column(String)
    content = Column(Text)
    importance = Column(Integer, default=0)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    embedding = Column(Text, nullable=True)
    category = Column(String, default="event")
