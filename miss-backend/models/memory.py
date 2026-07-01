# Copyright (C) 2026  MISS Project Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
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
