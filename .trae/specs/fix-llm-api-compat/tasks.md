# Tasks

- [ ] Task 1: 三级 fallback 架构重构（llm_caller.py）
  - [ ] SubTask 1.1: 将 `call()` 方法拆分为 `call()` 入口 + `_call_level1()` + `_call_level2()` + `_call_level3()`
  - [ ] SubTask 1.2: `_call_level1()`：当前 `Mode.TOOLS` 逻辑
    - 捕获 Exception 时记录 `logging.warning("[LLM] Level 1 (TOOLS) failed: {e}, falling back to Level 2...")`
  - [ ] SubTask 1.3: `_call_level2()`：`instructor.apatch(client, mode=instructor.Mode.JSON)` + `response_format={"type":"json_object"}`
    - 使用独立的 AsyncOpenAI 实例（不污染主 client）
    - 失败时记录 `logging.warning("[LLM] Level 2 (JSON mode) failed: {e}, falling back to Level 3...")`
  - [ ] SubTask 1.4: `_call_level3()`：裸 `AsyncOpenAI.chat.completions.create()`，无 instructor
    - 构造 messages（system prompt 中嵌入 JSON 输出格式指令 + one-shot 示例）
    - 从 `response.choices[0].message.content` 取文本 → `json.loads` 手动解析
    - 若 `json.loads` 失败 → 安全占位符（不原文透传，防止 system prompt 泄漏）
  - [ ] SubTask 1.5: 每个 API 调用完成后写入 INFO 日志：`[LLM] call complete: model={model}, level={N}, time={ms}ms`
  - [ ] SubTask 1.6: `analyze_character()` 对齐 fallback：至少加一级裸 API 降级（`json.loads` 失败 → 安全占位符），与 `call()` 的安全策略一致

- [ ] Task 2: 修复 `_ensure_client()` 推理模型检测
  - [ ] SubTask 2.1: `_is_reasoning_model()` 检测移到 `_get_instructor_mode()` 方法中
  - [ ] SubTask 2.2: Level 1 TOOLS 模式下，推理模型自动跳过 Level 1 → 直接走 Level 2 JSON

- [ ] Task 3: API 连接测试端点增强（routers/settings.py）
  - [ ] SubTask 3.1: `POST /api/settings/test` 改为发送实际消息 `{"messages": [{"role": "user", "content": "Hi"}], "max_tokens": 50}` → 验证完整链路（非仅 API Key 有效性）
  - [ ] SubTask 3.2: 测试结果返回 `{"ok": True/False, "response_time_ms": X, "level_used": N, "model": "xxx"}`

- [ ] Task 4: pytest 验证
  - [ ] SubTask 4.1: 更新 `test_llm_json_parse.py`：新增裸 API 返回非 JSON 的降级测试（`json.loads` 失败 → 原文当 spoken）
  - [ ] SubTask 4.2: 全量 pytest 无回归（183 基线）

# Task Dependencies
- Task 1 必须先做（是核心架构变更）
- Task 2 依赖 Task 1
- Task 3 可并行
- Task 4 依赖 Task 1-3

# 技术要点
- **三级 fallback 顺序**：TOOLS → JSON → Raw。TOOLS 失败自动降级，上层无感知
- **Raw 模式**：不使用 instructor 的 `response_model`，直接调 `AsyncOpenAI.chat.completions.create`
- **ST 风格兜底**：Level 3 成功时正常解析。`json.loads` 失败 → 安全占位符（不原文透传，防止 system prompt 泄漏或注入载荷）
- **日志格式**：`[LLM] Level N (MODE) {success/failure}: model={x}, time={y}ms` — 便于排查用户 API 配置问题
