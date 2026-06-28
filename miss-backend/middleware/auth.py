from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from config import config

PUBLIC_PATHS = {"/health", "/api/info", "/docs", "/redoc", "/openapi.json", "/favicon.ico"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/openapi.json"):
            return await call_next(request)

        if not config.access_token or config.access_token == "change-me-in-production":
            return await call_next(request)

        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer ") or auth[7:] != config.access_token:
            raise HTTPException(status_code=401, detail="未授权访问")

        return await call_next(request)
