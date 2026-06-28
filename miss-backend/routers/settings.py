import time
from fastapi import APIRouter, Request
from pydantic import BaseModel
from limiter import limiter
from config import apply_runtime_settings, get_runtime_settings

router = APIRouter()


class SettingsRequest(BaseModel):
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    model: str | None = None


class TestConnectionRequest(BaseModel):
    pass


@router.get("/settings")
@limiter.limit("30/minute")
async def get_settings(request: Request):
    return get_runtime_settings()


@router.post("/settings")
@limiter.limit("5/minute")
async def update_settings(request: Request, req: SettingsRequest):
    apply_runtime_settings({
        "openai_api_key": req.openai_api_key,
        "openai_base_url": req.openai_base_url,
        "model": req.model,
    })
    from routers.chat import _caller
    _caller.flush_client()
    return {"message": "设置已保存", "status": get_runtime_settings()}


@router.post("/settings/test")
@limiter.limit("3/minute")
async def test_connection(request: Request):
    from services.llm_caller import LLMCaller

    caller = LLMCaller()
    try:
        caller._ensure_client()
    except RuntimeError as e:
        return {"ok": False, "error": str(e), "response_time_ms": 0, "level_used": 0}

    model = get_runtime_settings().get("model", "gpt-4o")
    messages = [{"role": "user", "content": "Hi"}]
    start = time.time()

    try:
        resp = await caller.call(messages, model_config={"model": model, "max_tokens": 50})
        ms = int((time.time() - start) * 1000)
        level = 3 if resp.get("_error") else 1
        return {"ok": not resp.get("_error"), "response_time_ms": ms, "level_used": level, "model": model}
    except Exception as e:
        ms = int((time.time() - start) * 1000)
        return {"ok": False, "error": str(e)[:200], "response_time_ms": ms, "level_used": 0, "model": model}
