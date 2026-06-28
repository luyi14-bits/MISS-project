from .chat import router as chat_router
from .preset import router as preset_router
from .admin import router as admin_router
from .character import router as character_router

__all__ = ["chat_router", "preset_router", "admin_router", "character_router"]
