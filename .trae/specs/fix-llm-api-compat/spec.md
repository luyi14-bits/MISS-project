# fix-llm-api-compat Spec — API 兼容性 + 多级 fallback

## Why
用户反馈：API 测试显示成功，但发消息永远返回"抱歉我暂时无法回应"。根因链路：

```
instructor.Mode.TOOLS → 底层发送 tool_choice 参数
  → 中转站 API / 非 OpenAI 官方 API 不支持 tool_choice
    → 400 / 不兼容响应
      → L88 except Exception → 返回"抱歉，我暂时无法回应"
```

对照 SillyTavern（ST 酒馆）的做法：
- ST **不使用** instructor / tool calling / response_format
- ST 直接用裸 `POST /v1/chat/completions`（标准 OpenAI 协议）
- ST 把角色信息写在 `system` prompt 中，`content` 返回纯文本
- ST 依赖 prompt engineering 引导 LLM 输出期望格式，而非 tool_choice 强制约束

**结论**：MISS 需要在 `Mode.JSON`（response_format）和裸 API（纯 prompt 约束）两种路径上做多级降级，而非死绑 `instructor.Mode.TOOLS`。

## What Changes
- `llm_caller.py` 重构 `_ensure_client()` + `call()` 为三级 fallback：
  1. `Mode.TOOLS`（function calling，仅 OpenAI 官方/兼容 API 有效）→ 失败则降级
  2. `Mode.JSON`（`response_format={"type":"json_object"}`，部分 API 兼容；Claude proxy / 部分中转站不支持）→ 失败则降级
  3. **裸 API**（ST 模式：纯 `POST /v1/chat/completions`，无 instructor，prompt 约束 + `json.loads` 解析）
- 每次失败记录到 `miss.log`，携带模型名+错误类型
- `call()` 耗时统计写入日志（定位 API 慢/超时问题）

## Impact
- Affected specs: fix-binding-and-api（该 Spec 的任务 1 在做推理模型修复时应一并处理）
- Affected code: `miss-backend/services/llm_caller.py`（核心修改）
- 不改: `desktop_bridge.py`, `PythonBridge.cs`, WPF Views

---

## ADDED Requirements

### Requirement: 三级 API 调用 fallback
The system SHALL 在 `call()` 中按以下顺序尝试：

```
Level 1: instructor Mode.TOOLS (function calling)
  └─ fail → Level 2: instructor Mode.JSON (response_format={"type":"json_object"})
       └─ fail → Level 3: 裸 AsyncOpenAI.chat.completions.create (ST 风格)
            └─ fail → 返回 {"_error": True, "spoken": "抱歉..."}
```

每次降级时写入 `logging.warning("[LLM] Level N failed ({error}), falling back to Level {N+1}")`。

### Requirement: 裸 API 调用（ST 模式，Level 3）
不使用任何 instructor / tool_choice / response_format。发送纯 messages 到 `POST /v1/chat/completions`，从 `response.choices[0].message.content` 取文本，用 `json.loads` 手动解析。

```python
async def _call_raw(self, messages: list[dict], model: str) -> dict:
    """ST 风格：裸 API + prompt 约束 + json.loads"""
    raw_client = ...  # AsyncOpenAI without instructor patch
    resp = await raw_client.chat.completions.create(
        model=model, messages=messages,
        temperature=config.temperature, max_tokens=config.max_tokens,
    )
    content = resp.choices[0].message.content or ""
    try:
        parsed = json.loads(content)
        return {"inner_thought": parsed.get("inner_thought", ""), "spoken": parsed.get("spoken", "")}
    except json.JSONDecodeError:
        # SEC: 不使用原文当 spoken — 原文可能含 system prompt 泄漏或注入载荷
        return {"inner_thought": "", "spoken": "响应格式异常，请重试", "_error": True, "message": "Level 3 json.loads failed"}
```

### Requirement: API 响应日志
The system SHALL 在每次 `call()` 完成后写入一条 INFO 日志：`[LLM] call complete: model=xxx, level=N, time=XXms, tokens=X`

### Requirement: 测试连接端点增强
`POST /api/settings/test`（或等效逻辑）应发送一个简短消息（"Hello"）到 LLM 验证完整链路，而非仅 `GET /v1/models`。当前仅测试 API Key 有效性，不测试实际对话能力。

## SillyTavern API 架构参考

| 维度 | ST 做法 | MISS 当前 | MISS 修复后 |
|------|--------|---------|------------|
| 客户端 | 裸 `openai.ChatCompletion.create` | `instructor.apatch(client)` | 三级 fallback |
| 结构化输出 | prompt engineering + `json.loads` | `response_model=ChatResponse` | Tool → JSON → Raw |
| tool_choice | 不发送 | `Mode.TOOLS` 自动发送 | Level 1 仅 OpenAI 官方 |
| response_format | 不发送 | 不发送（Mode.TOOLS 不用） | Level 2 用 `{"type":"json_object"}` |
| 兼容性 | ✅ 所有 OpenAI 兼容 API | ❌ 仅 OpenAI 官方/支持 function calling 的 API | ✅ 全网 API |
