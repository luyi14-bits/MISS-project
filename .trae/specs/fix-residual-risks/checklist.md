# Checklist

## Task 1: 加密体系对齐 — memory_entries 加密
- [ ] `memory_summarizer._save_memory()` 写入前调用 `encrypt(content)`
- [ ] `memory_manager.get_memories()` 读取后调用 `decrypt(content)`
- [ ] `memory_manager.get_recent_context()` 读取后调用 `decrypt(content)`
- [ ] 旧明文记忆可正常读取向后兼容（decrypt 对无 `ENC_V1_` 前缀的数据返回原文）
- [ ] 写入密文后读取能还原到原文
- [ ] `pytest` 全量 190/190 无回归

## Task 2: Fernet 密钥持久化
- [ ] `crypto.py` 无模块级副作用（`_cipher = None`，`init_fernet()` 显式初始化）
- [ ] `main.py` lifespan 中调用 `init_fernet()`
- [ ] `pythonengineservice.cs` 检测 `fernet.key` 文件：存在则读取，不存在则生成
- [ ] `pythonengineservice.cs` 在 `Py.SetPythonHome()` 后设 `MISS_FERNET_KEY` 环境变量
- [ ] 首次启动后 `%APPDATA%/MISS/fernet.key` 存在且为 32 字节 base64
- [ ] 重启后加密/解密跨会话生效
- [ ] `dotnet build` 0 error

## Task 3: SSRF 防护 — base_url 校验
- [ ] `config.py` 有 `_validate_base_url()` 函数
- [ ] `https://api.openai.com/v1` → 通过
- [ ] `http://192.168.1.1:8080` → 清空（返回空字符串）
- [ ] `http://127.0.0.1:11434` → 清空
- [ ] `http://localhost` → 清空
- [ ] 非法 scheme（`ftp://` / `file://`）→ 抛出 ValueError
- [ ] `pytest` 全量 190/190 无回归

## Task 4: 辅助修复
- [ ] `requirements.txt` 包含 `instructor>=1.0.0`
- [ ] `memory_summarizer.py:L65` 日志为 `%s` 参数化格式
- [ ] `prompt_builder.py:L38` 日志为 `%s` 参数化格式
- [ ] `vector_store.py:L21` 日志为 `%s` 参数化格式
- [ ] `LoggingService.cs:Write()` 中 `message` 的 `\n` `\r` 被转义

## 验收
- [ ] 加密体系一致（messages + memory_entries 均加密）
- [ ] Fernet 密钥跨重启持久化
- [ ] 无 SSRF 攻击路径（base_url 被校验）
- [ ] `dotnet build` 0 error
- [ ] `pytest` 190/190
- [ ] 无明文 Key / Token 泄露
