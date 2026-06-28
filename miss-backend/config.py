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
        _runtime_overrides = {
            k: v for k, v in settings.items()
            if v is not None and v != ""
        }


def get_runtime_settings() -> dict:
    with _runtime_lock:
        return {
            "openai_api_key_set": bool(_runtime_overrides.get("openai_api_key") or config.openai_api_key),
            "openai_base_url": _runtime_overrides.get("openai_base_url", config.openai_base_url),
            "model": _runtime_overrides.get("model", config.model),
        }
