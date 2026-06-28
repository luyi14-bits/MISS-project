# Checklist

## Task 1: 三级 fallback 架构
- [ ] `call()` 方法拆分为入口 + 三个 `_call_levelN` 私有方法
- [ ] Level 1 (`Mode.TOOLS`)：保持现有逻辑，加 `logging.warning` 降级日志
- [ ] Level 2 (`Mode.JSON`)：独立 `AsyncOpenAI` + `response_format={"type":"json_object"}`
- [ ] Level 3 (裸 API / ST 模式)：无 instructor，直接调 `AsyncOpenAI.chat.completions.create`
- [ ] Level 3 `json.loads` 失败 → 安全占位符（不原文透传）
- [ ] 每次调用完成写入 `[LLM] call complete: model=x, level=N, time=Xms`

## Task 2: 推理模型处理
- [ ] `_is_reasoning_model()` 逻辑保持不变
- [ ] 推理模型自动跳过 Level 1（TOOLS）→ 从 Level 2（JSON）开始

## Task 3: 测试连接增强
- [ ] `POST /api/settings/test` 发真实消息（`{"messages": [...], "max_tokens": 50}`）
- [ ] 返回 `{"ok": true, "response_time_ms": X, "level_used": N}`

## Task 4: 回归测试
- [ ] `test_llm_json_parse.py` 新增裸 API 非 JSON 降级测试（验证安全占位符，非原文透传）
- [ ] pytest 183/183 全量通过

## 验收
- [ ] level=3（裸 API）调用成功，返回正确的 spoken + inner_thought
- [ ] level=2（JSON mode）失败时自动降级到 level=3
- [ ] `miss.log` 记录每次 API 调用的 level/model/time
- [ ] API 设置面板"测试连接"发送真实消息验证
