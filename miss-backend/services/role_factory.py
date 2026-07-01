# Copyright (C) 2026  MISS Project Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
import asyncio, logging
from pydantic import BaseModel, Field
from config import config, get_api_key, get_base_url, get_model
from openai import AsyncOpenAI
import instructor


class GeneratedRole(BaseModel):
    name: str = Field(description="角色名字，1-4 个中文字")
    description: str = Field(description="角色特征描述，50-100 字")
    background: str = Field(description="角色背景故事，100-200 字")
    tags: list[str] = Field(description="领域标签列表，从 ['科学','人文','艺术','技术','自然','幻想','日常','冒险'] 中选择")
    avatar_suggestion: str = Field(description="推荐头像描述，用于 AI 生成头像，约 20 字")
    rational_emotional: int = Field(default=0, ge=-100, le=100, description="理智→情绪")
    willpower: int = Field(default=0, ge=-100, le=100, description="意志力")
    independent_submissive: int = Field(default=0, ge=-100, le=100, description="独立→顺从")
    education_level: int = Field(default=0, ge=-100, le=100, description="文化水平")
    intimacy: int = Field(default=0, ge=0, le=100, description="亲密度")
    curiosity: int = Field(default=0, ge=-100, le=100, description="好奇心")
    humor: int = Field(default=0, ge=-100, le=100, description="幽默感")
    aggression: int = Field(default=0, ge=-100, le=100, description="攻击性")
    social_energy: int = Field(default=0, ge=-100, le=100, description="社交活力")
    adventurousness: int = Field(default=0, ge=-100, le=100, description="冒险精神")


class RoleFactory:
    def __init__(self):
        self._client = None

    def _ensure_client(self):
        if self._client is not None:
            return
        key = get_api_key()
        if not key:
            raise RuntimeError("请先配置 API Key")
        base = get_base_url()
        client = AsyncOpenAI(api_key=key, base_url=base) if base else AsyncOpenAI(api_key=key)
        self._client = instructor.apatch(client, mode=instructor.Mode.JSON)

    async def generate(self, seed_text: str) -> dict:
        self._ensure_client()
        model = get_model() or config.model
        try:
            resp: GeneratedRole = await asyncio.wait_for(
                self._client.chat.completions.create(
                    model=model,
                    messages=[{
                        "role": "user",
                        "content": f"根据以下种子文字生成一个完整的角色：\n\n{seed_text}\n\n生成角色的姓名、描述、背景故事、领域标签、头像建议和全部 10 维属性值。属性值必须符合人物设定。"
                    }],
                    response_model=GeneratedRole,
                    max_retries=2,
                ),
                timeout=60.0,
            )
            d = resp.model_dump()
            return {
                "name": d["name"],
                "description": d["description"],
                "background": d["background"],
                "tags": d["tags"],
                "avatar_suggestion": d["avatar_suggestion"],
                "profile": {k: d[k] for k in [
                    "rational_emotional", "willpower", "independent_submissive",
                    "education_level", "intimacy", "curiosity", "humor",
                    "aggression", "social_energy", "adventurousness"
                ]},
            }
        except asyncio.TimeoutError:
            return {"_error": True, "message": "角色生成超时"}
        except Exception as e:
            logging.getLogger("role_factory").warning("generate failed: %s", e)
            return {"_error": True, "message": f"角色生成失败: {str(e)}"}
