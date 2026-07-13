# Copyright (C) 2026  MISS Project Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
import asyncio
import json
import queue
import logging
from typing import Generator
from threading import Thread, Event

from routers.room import RoomChatRequest, _builder, _caller, _store, _filter, _intimacy_engine

logger = logging.getLogger(__name__)


def chat(session_id: str, message: str, characters: list[dict]) -> list[dict]:
    """Synchronous room chat wrapper for C# pythonnet bridge."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        req = RoomChatRequest(
            session_id=session_id,
            message=message,
            characters=characters,
        )
        result = loop.run_until_complete(_room_chat_impl(req))
        return result.get("responses", [])
    finally:
        loop.close()


async def _room_chat_impl(req: RoomChatRequest) -> dict:
    """Multi-character room chat implementation."""
    from fastapi import Request as FastAPIRequest

    async def call_for_character(char: dict) -> dict:
        profile_dict = char.get("profile", {})
        from services.attribute_engine import MISSProfile
        profile = MISSProfile(**profile_dict)
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

        try:
            result = await _caller.call(messages)
        except Exception:
            logger.error("Room LLM call failed for %s", char_name, exc_info=True)
            result = {"inner_thought": "...", "spoken": "嗯？"}

        result = _filter.filter_response(result, profile.education_level, profile.allowed_domains or None)
        intimacy = _intimacy_engine.evaluate(req.message, profile.intimacy)

        return {
            "character_name": char_name,
            "inner_thought": result.get("inner_thought", ""),
            "spoken": result.get("spoken", ""),
            "intimacy_change": intimacy["change"],
        }

    results = await asyncio.gather(*[call_for_character(c) for c in req.characters])

    _store.add_message(req.session_id, "user", req.message)
    for r in results:
        _store.add_message(req.session_id, f"character:{r['character_name']}", r["spoken"])

    return {"responses": results}


def chat_stream(session_id: str, message: str, characters: list[dict]) -> Generator[str, None, None]:
    """Synchronous room chat stream generator for C# pythonnet bridge.
    
    Yields SSE-like strings with character_start / character_end markers.
    """
    result_queue: queue.Queue = queue.Queue()
    done_event = Event()

    def run_stream():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_stream_impl(session_id, message, characters, result_queue))
        finally:
            loop.close()
            done_event.set()

    thread = Thread(target=run_stream, daemon=True)
    thread.start()

    while True:
        try:
            item = result_queue.get(timeout=0.5)
            if item is None:
                break
            yield item
        except queue.Empty:
            if done_event.is_set():
                break
            continue


async def _stream_impl(session_id: str, message: str, characters: list[dict], q: queue.Queue):
    """Async streaming implementation — sequential character responses."""
    from services.attribute_engine import MISSProfile

    _store.add_message(session_id, "user", message)

    for char in characters:
        char_name = char.get("name", "unknown")
        profile = MISSProfile(**char.get("profile", {}))
        background = char.get("background", "")
        spoken_full = ""

        ctx = _builder.build_room_prompt(
            session_id=session_id,
            user_message=message,
            profile=profile,
            character_name=char_name,
            room_characters=[c["name"] for c in characters],
            character_background=background,
        )
        msgs = ctx["messages"]

        q.put(json.dumps({"type": "character_start", "name": char_name}, ensure_ascii=False) + "\n\n")

        try:
            async for sse_line in _caller.stream(msgs):
                q.put(sse_line)
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
            _store.add_message(session_id, f"character:{char_name}", filtered)

        intimacy = _intimacy_engine.evaluate(message, profile.intimacy)
        q.put(json.dumps({"type": "character_end", "name": char_name, "spoken": spoken_full, "intimacy_change": intimacy["change"]}, ensure_ascii=False) + "\n\n")

    q.put(json.dumps({"type": "room_done"}) + "\n\n")
    q.put(None)
