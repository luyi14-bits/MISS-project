# Windows 启动方式: python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
# 若 uvicorn 命令找不到，请使用 python -m uvicorn 而非直接 uvicorn

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from database import init_db
from limiter import limiter
from middleware.auth import AuthMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

ALLOWED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://127.0.0.1:1420",
    "tauri://localhost",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="MISS Backend", version="0.1.0", lifespan=lifespan)

app.state.limiter = limiter


async def _rate_limit_handler(request, exc):
    from starlette.responses import JSONResponse
    return JSONResponse(status_code=429, content={"detail": "请求过于频繁，请稍后再试"})


app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)

app.add_middleware(AuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/api/info")
async def api_info():
    return {
        "name": "MISS Backend API",
        "version": "0.1.0",
        "endpoints": {
            "chat": {
                "POST /api/chat": "发送消息，返回双轨 JSON 响应",
                "POST /api/chat/stream": "发送消息，返回 SSE 流式响应",
            },
            "preset": {
                "GET /api/preset/list": "列出所有已保存预设",
                "POST /api/preset/save": "保存当前 profile 为预设",
                "GET /api/preset/{preset_id}": "读取指定预设",
                "DELETE /api/preset/{preset_id}": "删除预设",
                "POST /api/preset/apply": "应用预设到当前会话",
                "GET /api/preset/{preset_id}/export": "导出预设为 JSON 文件",
                "POST /api/preset/import": "从 JSON 文件导入预设",
            },
            "admin": {
                "GET /api/admin/stats": "系统统计信息",
                "POST /api/admin/memory/compact": "触发记忆压缩",
                "POST /api/admin/memory/age": "触发记忆老化清理",
            },
        },
        "docs": {
            "swagger": "/docs",
            "redoc": "/redoc",
        },
        "chat_request_schema": {
            "session_id": "string (UUID)",
            "message": "string",
            "profile": {
                "rational_emotional": "int (-100..100, default 0)",
                "willpower": "int (-100..100, default 0)",
                "independent_submissive": "int (-100..100, default 0)",
                "education_level": "int (-100..100, default 0)",
                "intimacy": "int (0..100, default 0)",
                "curiosity": "int (-100..100, default 0)",
                "humor": "int (-100..100, default 0)",
                "aggression": "int (-100..100, default 0)",
                "social_energy": "int (-100..100, default 0)",
                "adventurousness": "int (-100..100, default 0)",
                "allowed_domains": "list[str] (optional)",
            },
        },
        "chat_response_schema": {
            "inner_thought": "string (Track A 内心独白)",
            "spoken": "string (Track B 用户可见回复)",
            "active_easter_eggs": "list[str]",
            "active_cross_effects": "list[{id, persona_name, type}]",
        },
    }

from routers import chat, preset, admin, character
from routers.settings import router as settings_router
app.include_router(chat.router, prefix="/api")
app.include_router(preset.router, prefix="/api")
app.include_router(admin.router, prefix="/api/admin")
app.include_router(character.router, prefix="/api")
app.include_router(settings_router, prefix="/api")

frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
desktop_dir = os.environ.get("MISS_FRONTEND_DIR") or os.path.join(os.path.dirname(__file__), "frontend-desktop")
if os.path.isdir(desktop_dir):
    app.mount("/demo", StaticFiles(directory=desktop_dir, html=True), name="desktop")
if os.path.isdir(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("__main__:app", host="127.0.0.1", port=8000, log_level="warning")
