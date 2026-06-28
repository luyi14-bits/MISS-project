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


class ChatRequest(BaseModel):
    session_id: str = Field(max_length=64)
    message: str = Field(min_length=1, max_length=4000)
    profile: MISSProfile = MISSProfile()
    background: str = Field(default="", max_length=2000)


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


@router.post("/chat")
@limiter.limit("10/minute")
async def chat(request: Request, req: ChatRequest):
    ctx = _builder.build_full(req.session_id, req.message, req.profile, req.background)
    messages = ctx["messages"]
    active_easter_eggs = ctx["active_easter_eggs"]
    active_cross_effects = ctx["active_cross_effects"]

    if not _has_valid_key():
        result = _fallback_response(req.message, active_easter_eggs, active_cross_effects)
    else:
        try:
            _caller.flush_client()
            result = await _caller.call(messages)
        except Exception:
            logger.error("LLM API call failed", exc_info=True)
            result = _fallback_response(req.message, active_easter_eggs, active_cross_effects)

    if result.get("_error"):
        logger.warning("LLM responded with error: %s", result.get("_error"))

    result = _filter.filter_response(result, req.profile.education_level, req.profile.allowed_domains or None)

    _store.add_message(req.session_id, "user", req.message)
    _store.add_message(req.session_id, "assistant", result["spoken"])

    intimacy_result = _intimacy_engine.evaluate(req.message, req.profile.intimacy)
    new_intimacy = max(0, min(100, req.profile.intimacy + intimacy_result["change"]))

    return {
        "inner_thought": result["inner_thought"],
        "spoken": result["spoken"],
        "active_easter_eggs": active_easter_eggs,
        "active_cross_effects": active_cross_effects,
        "intimacy_change": intimacy_result["change"],
        "intimacy": new_intimacy,
        "intimacy_reason": intimacy_result["reason"],
    }


@router.post("/chat/stream")
@limiter.limit("10/minute")
async def chat_stream(request: Request, req: ChatRequest):
    ctx = _builder.build_full(req.session_id, req.message, req.profile, req.background)
    messages = ctx["messages"]
    spoken_full = ""

    async def event_generator():
        nonlocal spoken_full
        try:
            async for sse_line in _caller.stream(messages):
                yield sse_line
                if '"type":"token"' in sse_line:
                    try:
                        payload_str = sse_line.replace("data: ", "").strip()
                        payload = json.loads(payload_str)
                        spoken_full += payload.get("text", "")
                    except Exception:
                        logging.getLogger("chat").debug("stream token parse skipped: %s", sse_line[:80])
        except Exception:
            fallback = _fallback_response(req.message, ctx["active_easter_eggs"], ctx["active_cross_effects"])
            yield f"data: {json.dumps({'type': 'done', 'inner_thought': fallback['inner_thought'], 'spoken': fallback['spoken']}, ensure_ascii=False)}\n\n"
            spoken_full = fallback["spoken"]

        _store.add_message(req.session_id, "user", req.message)
        if spoken_full:
            filtered_spoken = _filter.filter(spoken_full, req.profile.education_level, req.profile.allowed_domains or None)
            _store.add_message(req.session_id, "assistant", filtered_spoken)

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
        return {
            "inner_thought": "这个问题好难...完全不懂。BAKA~",
            "spoken": "诶？你说什么...完全听不懂呢。BAKA~",
        }
    if cross_effects:
        persona_names = ", ".join(e["persona_name"] for e in cross_effects[:2])
        return {
            "inner_thought": f"当前处于{persona_names}模式，但暂时无法回应。",
            "spoken": "嗯...（内心正在处理信息）。请再说一遍？",
        }
    return {
        "inner_thought": "目前没有办法回应，但我在听。",
        "spoken": "嗯...我听到了。但现在好像有点说不出话来。",
    }
