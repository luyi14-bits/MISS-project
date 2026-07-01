# Copyright (C) 2026  MISS Project Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
"""
MISS Desktop Bridge — synchronous Python entry points for C# pythonnet.
All async LLM calls are wrapped with asyncio.new_event_loop() + run_until_complete().
Pydantic BridgeProfile enforces strict boundary validation. No bare dict.get().
"""
import os, sys, json, queue, threading, asyncio, logging, uuid
from typing import Dict, List, Any

from pydantic import BaseModel, Field


class BridgeProfile(BaseModel):
    rational_emotional: int = Field(default=0, ge=-100, le=100)
    willpower: int = Field(default=0, ge=-100, le=100)
    independent_submissive: int = Field(default=0, ge=-100, le=100)
    education_level: int = Field(default=0, ge=-100, le=100)
    intimacy: int = Field(default=0, ge=0, le=100)
    curiosity: int = Field(default=0, ge=-100, le=100)
    humor: int = Field(default=0, ge=-100, le=100)
    aggression: int = Field(default=0, ge=-100, le=100)
    social_energy: int = Field(default=0, ge=-100, le=100)
    adventurousness: int = Field(default=0, ge=-100, le=100)


# ── globals ──
_bridge_store = None
_prompt_builder = None
_llm_caller = None
_knowledge_filter = None
_intimacy_engine = None
_vector_store = None
_warnings: List[str] = []


def init(data_dir: str) -> Dict[str, Any]:
    """Call once from C# on startup. Sets paths, inits DB, downgrades ChromaDB if unavailable."""
    from .crypto import init_fernet
    init_fernet()

    global _bridge_store, _prompt_builder, _llm_caller, _knowledge_filter
    global _intimacy_engine, _vector_store, _warnings
    _warnings = []

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    os.makedirs(data_dir, exist_ok=True)

    inst_file = os.path.join(data_dir, ".instance")
    if os.path.exists(inst_file):
        with open(inst_file) as f:
            instance_id = f.read().strip()
    else:
        instance_id = uuid.uuid4().hex[:8]
        with open(inst_file, "w") as f:
            f.write(instance_id)

    inst_dir = os.path.join(data_dir, instance_id)
    os.makedirs(inst_dir, exist_ok=True)

    os.environ["MISS_DATA_DIR"] = inst_dir

    _backend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _backend not in sys.path:
        sys.path.insert(0, _backend)

    try:
        import pysqlite3
        sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
    except ImportError:
        pass

    from config import config as cfg
    db_path = os.path.join(inst_dir, "miss.db")
    cfg.db_url = f"sqlite:///{db_path}"

    from database import engine, SessionLocal
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL"))
        conn.execute(text("PRAGMA busy_timeout=30000"))
        conn.commit()

    from models import Base
    Base.metadata.create_all(bind=engine)

    from services.memory_manager import ConversationStore
    from services.prompt_builder import PromptBuilder
    from services.llm_caller import LLMCaller
    from services.attribute_engine import KnowledgeFilter, IntimacyEngine
    from config import get_api_key

    _bridge_store = ConversationStore()
    _llm_caller = LLMCaller()
    _knowledge_filter = KnowledgeFilter()
    _intimacy_engine = IntimacyEngine()

    if os.environ.get("MISS_NO_CHROMADB", "").lower() == "true":
        _vector_store = _FakeVectorStore()
        _warnings.append("chromadb unavailable — long-term memory disabled (explicit)")
    else:
        try:
            from services.vector_store import VectorMemoryStore
            _vector_store = VectorMemoryStore(api_key=get_api_key())
        except (ImportError, ModuleNotFoundError) as e:
            _vector_store = _FakeVectorStore()
            _warnings.append(f"chromadb unavailable — long-term memory disabled ({e})")
        except Exception as e:
            _vector_store = _FakeVectorStore()
            _warnings.append(f"chromadb unavailable — long-term memory disabled ({e})")

    _prompt_builder = PromptBuilder(vector_store=_vector_store)

    result: Dict[str, Any] = {"ok": True}
    if _warnings:
        result["warnings"] = _warnings
    return result


class _FakeVectorStore:
    def recall(self, query: str, top_k: int = 5) -> list:
        return []

    def recall_with_threshold(self, query: str, top_k: int = 5, threshold: float = 0.5) -> list:
        return []


# ── helpers ──

def _validate_profile(profile_dict: dict) -> BridgeProfile:
    try:
        return BridgeProfile(**profile_dict)
    except Exception as e:
        raise ValueError(f"C# 传入的角色属性字典校验失败: {str(e)}")


def _validate_message(message: str) -> str:
    if not isinstance(message, str):
        raise ValueError("message must be a string")
    msg = message.strip()
    if len(msg) < 1:
        raise ValueError("message is too short (min 1 char)")
    if len(msg) > 4000:
        raise ValueError("message is too long (max 4000 chars)")
    return msg


def _validate_session(session_id: str) -> str:
    if not isinstance(session_id, str) or len(session_id) > 64:
        raise ValueError("invalid session_id")
    return session_id


# ── public API ──

def chat(session_id: str, message: str, profile_dict: dict, background: str = "") -> dict:
    try:
        return _chat_inner(session_id, message, profile_dict, background)
    except Exception as e:
        return {"_error": True, "message": str(e)}


def _chat_inner(session_id: str, message: str, profile_dict: dict, background: str = "") -> dict:
    message = _validate_message(message)
    session_id = _validate_session(session_id)
    if background and len(background) > 2000:
        background = background[:2000]

    profile = _validate_profile(profile_dict)

    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(_do_chat(session_id, message, profile, background))
    finally:
        loop.close()


async def _do_chat(session_id: str, message: str, profile: BridgeProfile, background: str) -> dict:
    ctx = _prompt_builder.build_full(session_id, message, profile, background)
    result = await _llm_caller.call(ctx["messages"])

    result = _knowledge_filter.filter_response(result, profile.education_level)
    intimate = _intimacy_engine.evaluate(message, profile.intimacy)

    response = {
        "spoken": result.get("spoken", ""),
        "inner_thought": result.get("inner_thought", ""),
        "intimacy_change": intimate.get("change", 0),
        "intimacy": profile.intimacy + intimate.get("change", 0),
        "intimacy_reason": intimate.get("reason", ""),
        "active_easter_eggs": ctx.get("active_easter_eggs", []),
        "active_cross_effects": ctx.get("active_cross_effects", []),
    }
    if result.get("_error"):
        response["_error"] = True
        response["message"] = result.get("message", "")
    return response


def chat_stream(session_id: str, message: str, profile_dict: dict, background: str = ""):
    """Synchronous generator wrapping async LLM stream via Queue(maxsize=100) + daemon thread + threading.Event."""
    try:
        message = _validate_message(message)
        session_id = _validate_session(session_id)
        if background and len(background) > 2000:
            background = background[:2000]

        profile = _validate_profile(profile_dict)
    except Exception as e:
        # SEC: Must follow SSE protocol `data: ...\n\n` format.
        # Without `data:` prefix, C# MainViewModel.cs L365-369 treats the token
        # as raw text and renders the raw Python exception string to UI.
        error_payload = json.dumps({"_error": True, "message": str(e)}, ensure_ascii=False)
        yield f"data: {error_payload}\n\n"
        return

    q = queue.Queue(maxsize=100)
    stop_event = threading.Event()

    def _run_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            async def _stream():
                try:
                    ctx = _prompt_builder.build_full(session_id, message, profile, background)
                    async for chunk in _llm_caller.stream(ctx["messages"]):
                        if stop_event.is_set():
                            break
                        q.put(chunk, timeout=2.0)
                except Exception as e:
                    error_payload = json.dumps(
                        {"_error": True, "message": f"Python后台流处理崩溃: {str(e)}"},
                        ensure_ascii=False
                    )
                    q.put(f"data: {error_payload}\n\n")
                finally:
                    q.put(None)

            loop.run_until_complete(_stream())
        finally:
            loop.close()

    t = threading.Thread(target=_run_loop, daemon=True)
    t.start()

    try:
        while True:
            try:
                token = q.get(timeout=1.0)
            except queue.Empty:
                if stop_event.is_set():
                    break
                continue

            if token is None:
                break
            yield token
    finally:
        stop_event.set()
        t.join(timeout=2.0)


def analyze_character(description: str) -> Dict[str, int]:
    if len(description) > 2000:
        description = description[:2000]

    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_llm_caller.analyze_character(description))
    finally:
        loop.close()

    if "_error" in result:
        raise RuntimeError(result.get("message", "character analysis failed"))

    from routers.character import ATTR_META
    profile = {}
    for name, _, lo, hi in ATTR_META:
        val = int(result.get(name, 0))
        profile[name] = max(lo, min(hi, val))

    return profile


def ping_test() -> dict:
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(_ping_test())
    finally:
        loop.close()


async def _ping_test() -> dict:
    logger = logging.getLogger("desktop_bridge")
    try:
        messages = [{"role": "user", "content": "ping"}]
        result = await _llm_caller.call(messages)
        spoken = str(result.get("spoken", "")).lower()
        if "pong" in spoken:
            logger.info("[ping_test] 连接成功 — LLM 回复 pong")
            return {"ok": True, "message": "连接成功 ✅"}
        logger.info("[ping_test] 连接成功 — LLM 回复: %s", spoken[:80])
        return {"ok": True, "message": f"连接成功 ✅（回复: {spoken[:80]}）"}
    except Exception as e:
        logger.warning("[ping_test] 连接失败: %s", str(e)[:120])
        return {"ok": False, "message": f"连接失败: {str(e)[:120]}"}


def build_prompt(session_id: str, message: str, profile_dict: dict, background: str = "") -> dict:
    profile = _validate_profile(profile_dict)
    return _prompt_builder.build_full(session_id, message, profile, background)


def filter_response(result_dict: dict, education_level: int) -> dict:
    return _knowledge_filter.filter_response(result_dict, education_level)


def evaluate_intimacy(user_message: str, current_intimacy: int) -> dict:
    return _intimacy_engine.evaluate(user_message, current_intimacy)


def apply_settings(settings_dict: dict) -> None:
    from config import apply_runtime_settings as _apply
    _apply(settings_dict)
    _llm_caller.flush_client()


def get_runtime_settings() -> dict:
    from config import get_runtime_settings as _get
    return _get()
