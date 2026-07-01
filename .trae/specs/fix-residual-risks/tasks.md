# Tasks

- [ ] Task 1: 加密体系对齐 — memory_entries 加密
  - [ ] SubTask 1.1: `memory_summarizer.py:_save_memory()` 中调用 `encrypt(content)`
  - [ ] SubTask 1.2: `memory_manager.py:get_memories()` / `get_recent_context()` 中调用 `decrypt(content)`
  - [ ] SubTask 1.3: `memory_manager.py:get_recent_context()` 读取 `memory_entries` 的结果中也做解密
  - [ ] SubTask 1.4: `pytest` 验证记忆写入/读取加密一致性

- [ ] Task 2: Fernet 密钥持久化
  - [ ] SubTask 2.1: `crypto.py` 重构为惰性初始化（`_cipher = None` + `init_fernet()` 方法）
  - [ ] SubTask 2.2: `main.py` 的 `lifespan` 中调用 `init_fernet()`（后端模式）
  - [ ] SubTask 2.3: `pythonengineservice.cs` 启动时读取/生成 `fernet.key` → 设 `MISS_FERNET_KEY` 环境变量
  - [ ] SubTask 2.4: `pythonengineservice.cs` 中的 `Initialize()` 在 `Py.SetPythonHome()` 之后设置环境变量
  - [ ] SubTask 2.5: 验证桌面版启动后 `crypto.init_fernet()` 使用持久密钥

- [ ] Task 3: SSRF 防护 — base_url 校验
  - [ ] SubTask 3.1: `config.py` 增加 `_validate_base_url()` 函数
  - [ ] SubTask 3.2: `apply_runtime_settings()` 中对 `openai_base_url` 调用校验
  - [ ] SubTask 3.3: 验证 `127.0.0.1` / `192.168.x.x` / `api.openai.com` 三种场景

- [ ] Task 4: 辅助修复（低风险）
  - [ ] SubTask 4.1: `requirements.txt` 新增 `instructor>=1.0.0`
  - [ ] SubTask 4.2: `memory_summarizer.py:L65` f-string → `%s` 参数化
  - [ ] SubTask 4.3: `prompt_builder.py:L38` f-string → `%s` 参数化
  - [ ] SubTask 4.4: `vector_store.py:L21` f-string → `%s` 参数化
  - [ ] SubTask 4.5: `LoggingService.cs:Write()` 增加 `message.Replace("\n","\\n").Replace("\r","\\r")`

# Task Dependencies
- Task 2 必须先做（crypto.py 重构为惰性初始化为 Task 1 提供加密能力）
- Task 3 和 Task 4 可并行（与 Task 1/2 互不依赖）

# 工时估算
| Task | 子任务数 | 估算人天 | 说明 |
|------|---------|---------|------|
| Task 1 | 4 | 0.3 | 记忆加密对齐 |
| Task 2 | 5 | 0.4 | Fernet 密钥持久化（含 C# 改动） |
| Task 3 | 3 | 0.2 | SSRF 防护 |
| Task 4 | 5 | 0.15 | 辅助修复（低风险） |
| **合计** | **17** | **1.05** | |
