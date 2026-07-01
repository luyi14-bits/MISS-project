# Copyright (C) 2026  MISS Project Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
import logging
from urllib.parse import urlparse
from threading import Lock
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    openai_api_key: str = ""
    openai_base_url: str = ""
    db_url: str = "sqlite:///./miss.db"
    vector_db_path: str = "./vector_db"
    model: str = "gpt-4o"
    temperature: float = 1.0
    top_p: float = 0.92
    max_tokens: int = 1024
    frequency_penalty: float = 0.1
    conversation_window_size: int = 20
    access_token: str = ""

config = Settings()

# 运行时覆盖（前端设置面板写入，重启后失效）
_runtime_lock = Lock()
_runtime_overrides: dict = {}

_PRIVATE_NET_PREFIXES = (
    "10.", "192.168.", "172.16.", "172.17.", "172.18.", "172.19.",
    "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
    "172.25.", "172.26.", "172.27.", "172.28.", "172.29.",
    "172.30.", "172.31.",
)

_BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}


def _validate_base_url(url: str) -> str:
    if not url:
        return url
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"base_url scheme must be http or https: {parsed.scheme}")
    host = parsed.hostname or ""
    if host in _BLOCKED_HOSTS:
        logging.warning("[SSRF] base_url 指向本地地址 (%s)，已清除", host)
        return ""
    if any(host.startswith(p) for p in _PRIVATE_NET_PREFIXES):
        logging.warning("[SSRF] base_url 指向内网地址 (%s)，已清除", host)
        return ""
    return url


def get_api_key():
    with _runtime_lock:
        return _runtime_overrides.get("openai_api_key") or config.openai_api_key


def get_base_url():
    with _runtime_lock:
        return _runtime_overrides.get("openai_base_url") or config.openai_base_url or None


def get_model():
    with _runtime_lock:
        return _runtime_overrides.get("model") or config.model


def apply_runtime_settings(settings: dict):
    global _runtime_overrides
    with _runtime_lock:
        filtered = {}
        for k, v in settings.items():
            if v is None or v == "":
                continue
            if k == "openai_base_url":
                v = _validate_base_url(v)
            filtered[k] = v
        _runtime_overrides = filtered


def get_runtime_settings() -> dict:
    with _runtime_lock:
        return {
            "openai_api_key_set": bool(_runtime_overrides.get("openai_api_key") or config.openai_api_key),
            "openai_base_url": _runtime_overrides.get("openai_base_url", config.openai_base_url),
            "model": _runtime_overrides.get("model", config.model),
        }
