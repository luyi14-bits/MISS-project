# Copyright (C) 2026  MISS Project Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
from sqlalchemy import Column, String, DateTime, Text
from datetime import datetime, timezone

from models import Base


class Preset(Base):
    __tablename__ = "presets"

    id = Column(String, primary_key=True)
    name = Column(String, default="未命名预设")
    profile_json = Column(Text, default="{}")
    background = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
