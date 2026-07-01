# Copyright (C) 2026  MISS Project Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
from .chat import router as chat_router
from .preset import router as preset_router
from .admin import router as admin_router
from .character import router as character_router

__all__ = ["chat_router", "preset_router", "admin_router", "character_router"]
