# Copyright (C) 2026  MISS Project Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
import asyncio
import json
import logging
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from limiter import limiter
from services.attribute_engine import MISSProfile, KnowledgeFilter, IntimacyEngine
from services.prompt_builder import PromptBuilder
from services.llm_caller import LLMCaller
from services.memory_manager import ConversationStore
from config import get_api_key

logger = logging.getLogger(__name__)


class RoomChatRequest(BaseModel):
    session_id: str = Field(max_length=64)
    message: str = Field(min_length=1, max_length=4000)
    characters: list[dict] = Field(description="List of {name, profile, background} per character")


router = APIRouter()
_builder = PromptBuilder()
_caller = LLMCaller()
_store = ConversationStore()
_filter = KnowledgeFilter()
_intimacy_engine = IntimacyEngine()


def _has_valid_key():
    key = get_api_key()
    if not key:
        return False
    if key == "sk-placeholder" or key == "your_openai_api_key_here":
        return False
    return True


@router.post("/room/chat")
@limiter.limit("10/minute")
async def room_chat(request: Request, req: RoomChatRequest):
    """Multi-character room chat: parallel LLM calls, one response per character."""
    if not req.characters:
        return {"error": "no_characters", "detail": "Room must have at least one character"}

    async def call_for_character(char: dict) -> dict:
        profile = MISSProfile(**char.get("profile", {}))
        background = char.get("background", "")
        char_name = char.get("name", "unknown")

        ctx = _builder.build_room_prompt(
            session_id=req.session_id,
            user_message=req.message,
            profile=profile,
            character_name=char_name,
            room_characters=[c["name"] for c in req.characters],
            character_background=background,
        )
        messages = ctx["messages"]

        if not _has_valid_key():
            result = _fallback_response(req.message, ctx.get("active_easter_eggs", []), ctx.get("active_cross_effects", []))
        else:
            try:
                result = await _caller.call(messages)
            except Exception:
                logger.error("Room LLM call failed for %s", char_name, exc_info=True)
                result = _fallback_response(req.message, ctx.get("active_easter_eggs", []), ctx.get("active_cross_effects", []))

        result = _filter.filter_response(result, profile.education_level, profile.allowed_domains or None)
        intimacy_result = _intimacy_engine.evaluate(req.message, profile.intimacy)

        return {
            "character_name": char_name,
            "inner_thought": result.get("inner_thought", ""),
            "spoken": result.get("spoken", ""),
            "intimacy_change": intimacy_result["change"],
            "intimacy": max(0, min(100, profile.intimacy + intimacy_result["change"])),
        }

    # Parallel LLM calls
    results = await asyncio.gather(*[call_for_character(c) for c in req.characters])

    # Store user message and each character's response
    _store.add_message(req.session_id, "user", req.message)
    for r in results:
        _store.add_message(req.session_id, f"character:{r['character_name']}", r["spoken"])

    return {"responses": results}


@router.post("/room/chat/stream")
@limiter.limit("10/minute")
async def room_chat_stream(request: Request, req: RoomChatRequest):
    """Streaming multi-character room chat — characters respond sequentially with SSE identification."""

    async def event_generator():
        if not req.characters:
            yield f"data: {json.dumps({'type': 'error', 'detail': 'no_characters'})}\n\n"
            return

        _store.add_message(req.session_id, "user", req.message)

        for char in req.characters:
            char_name = char.get("name", "unknown")
            profile = MISSProfile(**char.get("profile", {}))
            background = char.get("background", "")
            spoken_full = ""

            ctx = _builder.build_room_prompt(
                session_id=req.session_id,
                user_message=req.message,
                profile=profile,
                character_name=char_name,
                room_characters=[c["name"] for c in req.characters],
                character_background=background,
            )
            messages = ctx["messages"]

            # Yield start marker
            yield f"data: {json.dumps({'type': 'character_start', 'name': char_name}, ensure_ascii=False)}\n\n"

            try:
                async for sse_line in _caller.stream(messages):
                    yield sse_line
                    if '"type":"token"' in sse_line:
                        try:
                            payload_str = sse_line.replace("data: ", "").strip()
                            payload = json.loads(payload_str)
                            spoken_full += payload.get("text", "")
                        except Exception:
                            pass
            except Exception:
                logger.error("Room stream failed for %s", char_name, exc_info=True)

            if spoken_full:
                filtered = _filter.filter(spoken_full, profile.education_level, profile.allowed_domains or None)
                _store.add_message(req.session_id, f"character:{char_name}", filtered)

            # Yield end marker
            intimacy_result = _intimacy_engine.evaluate(req.message, profile.intimacy)
            yield f"data: {json.dumps({'type': 'character_end', 'name': char_name, 'spoken': spoken_full or '...', 'intimacy_change': intimacy_result['change']}, ensure_ascii=False)}\n\n"

        # Yield room done
        yield f"data: {json.dumps({'type': 'room_done'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _fallback_response(user_message: str, eggs: list[str], cross_effects: list[dict]) -> dict:
    if "cirno_mode" in eggs:
        return {"inner_thought": "BAKA~", "spoken": "诶？BAKA~"}
    if cross_effects:
        persona = ", ".join(e["persona_name"] for e in cross_effects[:2])
        return {"inner_thought": f"{persona}模式", "spoken": "嗯...请再说一遍？"}
    return {"inner_thought": "无法回应", "spoken": "嗯...让我想想。"}
