# Copyright (C) 2026  MISS Project Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
import json
import asyncio
import time
import logging
from typing import AsyncGenerator
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
import instructor
from config import config, get_api_key, get_base_url, get_model

logger = logging.getLogger("llm_caller")


class ChatResponse(BaseModel):
    inner_thought: str = Field(
        default="",
        description="角色的内心独白，绝对不能留空。如果没有特殊想法也要写符合角色性格的心理活动"
    )
    spoken: str = Field(
        default="",
        description="角色实际说出口的话，必须直接输出内容，不要包含格式化标签或 markdown"
    )


class AnalysisResult(BaseModel):
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


_REASONING_MODELS = {"reasoner", "o1", "o3", "v4-pro", "v4-flash"}


def _is_reasoning_model(model: str) -> bool:
    return any(kw in model.lower() for kw in _REASONING_MODELS)


class LLMCaller:
    def __init__(self, api_key: str | None = None):
        self._api_key = api_key
        self._client = None
        self._max_retries = 2

    def _ensure_client(self):
        if self._client is not None:
            return
        key = self._api_key or get_api_key()
        if not key or key == "sk-placeholder" or key == "your_openai_api_key_here":
            raise RuntimeError("请先配置 API Key（点击右上角 ⚙ 设置）")
        base = get_base_url()
        client = AsyncOpenAI(api_key=key, base_url=base) if base else AsyncOpenAI(api_key=key)
        current_model = get_model() or config.model
        mode = instructor.Mode.JSON if _is_reasoning_model(current_model) else instructor.Mode.TOOLS
        self._client = instructor.apatch(client, mode=mode)

    def flush_client(self):
        self._client = None

    async def call(self, messages: list[dict], model_config: dict | None = None) -> dict:
        self._ensure_client()
        if model_config is None:
            model_config = {}
        model = model_config.get("model") or get_model() or config.model

        # DeepSeek/o1/o3: skip instructor, go raw API
        if _is_reasoning_model(model):
            return await self._call_raw(messages, model_config)

        start = time.time()

        try:
            resp: ChatResponse = await asyncio.wait_for(
                self._client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=model_config.get("temperature", config.temperature),
                    top_p=model_config.get("top_p", config.top_p),
                    max_tokens=model_config.get("max_tokens", config.max_tokens),
                    response_model=ChatResponse,
                    max_retries=self._max_retries,
                ),
                timeout=60.0,
            )
            ms = int((time.time() - start) * 1000)
            logger.info("[LLM] call complete: model=%s, level=1, time=%dms", model, ms)
            return resp.model_dump()
        except (asyncio.TimeoutError, RuntimeError) as e:
            logger.warning("[LLM] Level 1 failed (%s: %s), falling back to Level 2...", type(e).__name__, e)
        except Exception as e:
            logger.warning("[LLM] Level 1 failed (%s: %s), falling back to Level 2...", type(e).__name__, e)

        try:
            key = self._api_key or get_api_key()
            base = get_base_url()
            l2_client = AsyncOpenAI(api_key=key, base_url=base) if base else AsyncOpenAI(api_key=key)
            l2_resp = await asyncio.wait_for(
                l2_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=model_config.get("temperature", config.temperature),
                    max_tokens=model_config.get("max_tokens", config.max_tokens),
                    response_format={"type": "json_object"},
                ),
                timeout=60.0,
            )
            parsed = json.loads(l2_resp.choices[0].message.content or "{}")
            ms = int((time.time() - start) * 1000)
            logger.info("[LLM] call complete: model=%s, level=2, time=%dms", model, ms)
            return {"inner_thought": str(parsed.get("inner_thought", "")), "spoken": str(parsed.get("spoken", ""))}
        except Exception as e:
            logger.warning("[LLM] Level 2 failed (%s: %s), falling back to Level 3...", type(e).__name__, e)

        try:
            key = self._api_key or get_api_key()
            base = get_base_url()
            l3_client = AsyncOpenAI(api_key=key, base_url=base) if base else AsyncOpenAI(api_key=key)
            l3_messages = [
                {
                    "role": "system",
                    "content": (
                        "你必须只回复一个 JSON 对象，格式严格如下：\n"
                        '{"inner_thought": "角色的内心独白", "spoken": "角色说出口的话"}\n'
                        "禁止输出任何非 JSON 内容，禁止添加 markdown 代码块标记。"
                    ),
                },
                *messages,
            ]
            l3_resp = await asyncio.wait_for(
                l3_client.chat.completions.create(
                    model=model,
                    messages=l3_messages,
                    temperature=model_config.get("temperature", config.temperature),
                    max_tokens=model_config.get("max_tokens", config.max_tokens),
                ),
                timeout=60.0,
            )
            content = (l3_resp.choices[0].message.content or "")[:10000]
            try:
                parsed = json.loads(content)
                ms = int((time.time() - start) * 1000)
                logger.info("[LLM] call complete: model=%s, level=3, time=%dms", model, ms)
                return {"inner_thought": str(parsed.get("inner_thought", "")), "spoken": str(parsed.get("spoken", ""))}
            except json.JSONDecodeError:
                logger.warning("[LLM] Level 3 json.loads failed, returning safe placeholder")
                return {
                    "inner_thought": "",
                    "spoken": "响应格式异常，请检查 API 配置或重试",
                    "_error": True,
                    "message": "Level 3 json.loads failed",
                }
        except asyncio.TimeoutError:
            logger.warning("[LLM] Level 3 timeout")
            return {"inner_thought": "", "spoken": "抱歉，响应超时，请稍后再试。", "_error": True, "message": "LLM API 调用超时"}
        except RuntimeError as e:
            logger.warning("[LLM] Level 3 RuntimeError: %s", e)
            return {"inner_thought": "", "spoken": "抱歉，服务未就绪。请检查 API 配置。", "_error": True, "message": str(e)}
        except Exception as e:
            logger.warning("[LLM] Level 3 failed: %s", e)
            return {"inner_thought": "", "spoken": "抱歉，我暂时无法回应。请稍后再试。", "_error": True, "message": str(e)}

    async def analyze_character(self, description: str) -> dict:
        self._ensure_client()
        from routers.character import ATTR_META

        attr_lines = "\n".join(
            f"- {name}: {label} (范围 {lo}~{hi})"
            for name, label, lo, hi in ATTR_META
        )

        prompt = f"""分析以下角色描述，输出 JSON 格式的 10 维属性。

属性定义：
{attr_lines}

角色描述：
{description}
"""
        messages = [{"role": "user", "content": prompt}]
        model = get_model() or config.model

        try:
            response: AnalysisResult = await asyncio.wait_for(
                self._client.chat.completions.create(
                    model=model,
                    messages=messages,
                    response_model=AnalysisResult,
                    max_retries=self._max_retries,
                ),
                timeout=60.0,
            )
            return response.model_dump()
        except Exception as e:
            logger.warning("[analyze_character] Level 1 failed (%s: %s), falling back to Level 2...", type(e).__name__, e)
            try:
                key = self._api_key or get_api_key()
                base = get_base_url()
                l2_client = AsyncOpenAI(api_key=key, base_url=base) if base else AsyncOpenAI(api_key=key)
                l2_resp = await asyncio.wait_for(
                    l2_client.chat.completions.create(
                        model=model,
                        messages=messages,
                        response_format={"type": "json_object"},
                    ),
                    timeout=30.0,
                )
                parsed = json.loads(l2_resp.choices[0].message.content or "{}")
                return {name: parsed.get(name, 0) for name, _, _, _ in ATTR_META}
            except Exception as e:
                logging.getLogger("llm_caller").warning("[analyze_character] Level 2 failed: %s", e)
                try:
                    key = self._api_key or get_api_key()
                    base = get_base_url()
                    l3_client = AsyncOpenAI(api_key=key, base_url=base) if base else AsyncOpenAI(api_key=key)
                    l3_messages = [
                        {"role": "system", "content": (
                            "你必须只回复一个 JSON 对象，格式严格如下：\n"
                            '{"rational_emotional": 0, "willpower": 0, "independent_submissive": 0, '
                            '"education_level": 0, "intimacy": 0, "curiosity": 0, "humor": 0, '
                            '"aggression": 0, "social_energy": 0, "adventurousness": 0}\n'
                            "禁止输出任何非 JSON 内容。"
                        )},
                        *messages,
                    ]
                    l3_resp = await asyncio.wait_for(
                        l3_client.chat.completions.create(model=model, messages=l3_messages),
                        timeout=30.0,
                    )
                    content = (l3_resp.choices[0].message.content or "")[:5000]
                    parsed = json.loads(content)
                    return {name: parsed.get(name, 0) for name, _, _, _ in ATTR_META}
                except Exception as e:
                    logger.warning("[analyze_character] Level 3 failed: %s", e)
                    return {"_error": True, "message": "角色分析失败，请检查 API 配置"}

    async def stream(self, messages: list[dict], model_config: dict | None = None) -> AsyncGenerator[str, None]:
        self._ensure_client()
        if model_config is None:
            model_config = {}

        model = model_config.get("model") or get_model() or config.model

        # DeepSeek/o1 等推理模型流式不支持 instructor response_model，直接走裸 API
        if _is_reasoning_model(model):
            async for chunk in self._raw_stream(messages, model_config):
                yield chunk
            return

        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": model_config.get("temperature", config.temperature),
            "top_p": model_config.get("top_p", config.top_p),
            "max_tokens": model_config.get("max_tokens", config.max_tokens),
            "stream": True,
        }

        try:
            response = await self._client.chat.completions.create(**kwargs)
            full_text = ""
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    full_text += token
                    yield f"data: {json.dumps({'type': 'token', 'text': token}, ensure_ascii=False)}\n\n"

            parsed = self._parse_json_response(full_text)
            payload = json.dumps({
                "type": "done",
                "inner_thought": parsed["inner_thought"],
                "spoken": parsed["spoken"],
            }, ensure_ascii=False)
            yield f"data: {payload}\n\n"
            return
        except Exception as e:
            yield f"data: {json.dumps({'_error': True, 'message': str(e)[:200]}, ensure_ascii=False)}\n\n"

        # Level 2/3 fallback: raw API stream without instructor
        async for chunk in self._raw_stream(messages, model_config):
            yield chunk

    async def _raw_stream(self, messages: list[dict], model_config: dict | None = None) -> AsyncGenerator[str, None]:
        """直接裸 API 流式，跳过 instructor。用于 DeepSeek 等推理模型。"""
        if model_config is None:
            model_config = {}
        key = self._api_key or get_api_key()
        base = get_base_url()
        model = model_config.get("model") or get_model() or config.model
        raw_client = AsyncOpenAI(api_key=key, base_url=base) if base else AsyncOpenAI(api_key=key)
        try:
            response = await raw_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=model_config.get("temperature", config.temperature),
                max_tokens=model_config.get("max_tokens", config.max_tokens),
                stream=True,
            )
            full_text = ""
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    full_text += token
                    yield f"data: {json.dumps({'type': 'token', 'text': token}, ensure_ascii=False)}\n\n"

            parsed = self._parse_json_response(full_text)
            payload = json.dumps({
                "type": "done",
                "inner_thought": parsed["inner_thought"],
                "spoken": parsed["spoken"],
            }, ensure_ascii=False)
            yield f"data: {payload}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'_error': True, 'message': str(e)[:200]}, ensure_ascii=False)}\n\n"

    async def _call_raw(self, messages: list[dict], model_config: dict | None = None) -> dict:
        """直接裸 API 调用，不经过 instructor。用于 DeepSeek 等推理模型。"""
        if model_config is None:
            model_config = {}
        key = self._api_key or get_api_key()
        base = get_base_url()
        model = model_config.get("model") or get_model() or config.model
        start = time.time()

        # Level 1: json_object mode
        try:
            client = AsyncOpenAI(api_key=key, base_url=base) if base else AsyncOpenAI(api_key=key)
            resp = await asyncio.wait_for(
                client.chat.completions.create(
                    model=model, messages=messages,
                    temperature=model_config.get("temperature", config.temperature),
                    max_tokens=model_config.get("max_tokens", config.max_tokens),
                    response_format={"type": "json_object"},
                ), timeout=60.0)
            parsed = json.loads(resp.choices[0].message.content or "{}")
            ms = int((time.time() - start) * 1000)
            logger.info("[LLM] _call_raw L1: model=%s, time=%dms", model, ms)
            return {"inner_thought": str(parsed.get("inner_thought", "")), "spoken": str(parsed.get("spoken", ""))}
        except Exception as e:
            logger.warning("[LLM] _call_raw L1 failed (%s: %s), fallback L2", type(e).__name__, e)

        # Level 2: system-prefixed JSON instruction
        try:
            client = AsyncOpenAI(api_key=key, base_url=base) if base else AsyncOpenAI(api_key=key)
            l2_messages = [
                {"role": "system", "content": '你必须只回复一个JSON: {"inner_thought":"内心独白","spoken":"说出口的话"}'},
                *messages,
            ]
            resp = await asyncio.wait_for(
                client.chat.completions.create(
                    model=model, messages=l2_messages,
                    temperature=model_config.get("temperature", config.temperature),
                    max_tokens=model_config.get("max_tokens", config.max_tokens),
                ), timeout=60.0)
            content = (resp.choices[0].message.content or "")[:10000]
            parsed = json.loads(content)
            ms = int((time.time() - start) * 1000)
            logger.info("[LLM] _call_raw L2: model=%s, time=%dms", model, ms)
            return {"inner_thought": str(parsed.get("inner_thought", "")), "spoken": str(parsed.get("spoken", ""))}
        except json.JSONDecodeError:
            logger.warning("[LLM] _call_raw L2 json parse failed, content[:200]=%s", content[:200] if 'content' in dir() else 'N/A')
            return {"inner_thought": "", "spoken": "响应格式异常，请重试", "_error": True}
        except Exception as e:
            logger.warning("[LLM] _call_raw L2 failed: %s", e)
            return {"inner_thought": "", "spoken": "抱歉，我暂时无法回应。请稍后再试。", "_error": True, "message": str(e)[:200]}

    @staticmethod
    def _parse_json_response(raw: str) -> dict:
        if not raw or not raw.strip():
            return {"inner_thought": "", "spoken": ""}
        try:
            parsed = json.loads(raw.strip())
            if not isinstance(parsed, dict):
                raise json.JSONDecodeError("expected JSON object", raw, 0)
            return {
                "inner_thought": str(parsed.get("inner_thought", "")),
                "spoken": str(parsed.get("spoken", "")),
            }
        except json.JSONDecodeError:
            logger.warning(
                "stream JSON parse failed, raw text (length=%d) discarded to prevent injection", len(raw)
            )
            return {"inner_thought": "", "spoken": "响应格式异常，请重试"}
