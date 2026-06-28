from sqlalchemy import Column, String, DateTime, Integer
from datetime import datetime, timezone

from models import Base

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    title = Column(String, default="新对话")
