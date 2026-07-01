# fix-residual-risks — 加密体系对齐 + SSRF 防护 Spec

## Meta
- **优先级**: P1
- **估算工时**: 1.0 人天
- **影响 Spec**: 无（纯安全加固）
- **影响代码**: config.py · crypto.py · memory_summarizer.py · desktop_bridge.py · LiteDbLocalStore.cs · pythonengineservice.cs · requirements.txt

## Why
经过安全学院 5 轮审计（38 项修复），项目已达到 A- 安全等级。终审发现 4 项中危残余风险——它们不是新增漏洞，而是前 5 轮审计中没有覆盖到的防御深度问题：

1. **加密体系不一致** — 消息表已 Fernet 加密，但 `memory_entries`（记忆摘要表）以明文落盘。用户对话中最重要的长期记忆反而没有保护。
2. **Fernet 密钥不持久化** — `crypto.py` 在 `MISS_FERNET_KEY` 未设置时每次启动生成新密钥，导致所有加密数据重启后不可解密。WPF 桌面版默认不设置此变量。
3. **SSRF 攻击面** — `openai_base_url` 从用户输入到 `AsyncOpenAI(base_url=...)` 零校验，恶意本地应用可通过设置面板操纵 MISS 向任意内网服务器发起 HTTP 请求。
4. **依赖声明缺失** — `instructor` 包被 4 处代码直接使用但未在 `requirements.txt` 中声明。

## What Changes
- R02: `memory_summarizer.py` 的 `_save_memory()` 中 content 字段调用 `crypto.encrypt()` 加密
- R02: `memory_manager.py` 的 `get_memories()` / `get_recent_context()` 中 content 字段调用 `crypto.decrypt()` 解密
- R02: `vector_store.py` 的 `store()` 中 content 保持加密文本（向量库只存摘要嵌入向量）
- R05: `crypto.py` 模块级初始化改为惰性初始化（`init_fernet()`），确保只执行一次；桌面版 `pythonengineservice.cs` 启动时自动生成并持久化 `MISS_FERNET_KEY` 到 `%APPDATA%/MISS/fernet.key`
- R01: `config.py` 增加 `_validate_base_url()` 校验：禁止私有 IP、localhost、0.0.0.0、内网段；`apply_runtime_settings()` 中调用
- R09: `requirements.txt` 新增 `instructor>=1.0.0` 声明
- R11: 3 处 f-string 日志改为 `%s` 参数化格式（`memory_summarizer.py:L65` · `prompt_builder.py:L38` · `vector_store.py:L21`）
- R12: `LoggingService.cs` 增加 `message.Replace("\n","\\n").Replace("\r","\\r")` 转义

## Impact
- Affected specs: 无
- Affected code: `miss-backend/services/` (4 文件) + `miss-desktop-wpf/Services/` (2 文件)
- 不破坏任何现有 API 结构或接口

---

## ADDED Requirements

### Requirement: R02 — 记忆摘要加密对齐
The system SHALL 对 `memory_entries` 表中的 `content` 字段使用与 `messages` 表相同的 Fernet 加密方案。

```python
# memory_summarizer.py _save_memory
from services.crypto import encrypt, decrypt

content = encrypt(content)  # 写前加密

# memory_manager.py get_memories / get_recent_context
content = decrypt(content) if entry.content else ""  # 读后解密
```

#### Scenario: 记忆写加密
- **WHEN** `MemorySummarizer._save_memory()` 被调用
- **THEN** 写入 `memory_entries.content` 的值为 `ENC_V1_gAAAA...` 密文

#### Scenario: 已加密记忆正常读取
- **WHEN** `MemoryEntry` 从数据库读取并通过 `decrypt()` 解密
- **THEN** 返回原始明文内容

#### Scenario: 向后兼容已有明文记忆
- **WHEN** 数据库中已有未加密的旧记忆（无 `ENC_V1_` 前缀）
- **THEN** `decrypt()` 直接返回原文（已有逻辑）

### Requirement: R05 — Fernet 密钥持久化
The system SHALL 在桌面版启动时自动管理 `MISS_FERNET_KEY`：
- 检测 `%APPDATA%/MISS/fernet.key` 是否存在
- 存在 → 读取作为 `MISS_FERNET_KEY` 传给 Python
- 不存在 → 生成新密钥写入该文件，再传给 Python

```csharp
// pythonengineservice.cs
var fernetKeyPath = Path.Combine(appDataPath, "MISS", "fernet.key");
if (File.Exists(fernetKeyPath))
{
    var key = await File.ReadAllTextAsync(fernetKeyPath);
    _pythonEnv["MISS_FERNET_KEY"] = key.Trim();
}
else
{
    var key = GenerateFernetKey();  // 32 bytes base64
    Directory.CreateDirectory(Path.GetDirectoryName(fernetKeyPath)!);
    await File.WriteAllTextAsync(fernetKeyPath, key);
    _pythonEnv["MISS_FERNET_KEY"] = key;
}
```

`crypto.py` 修改为惰性初始化（模块级不做任何初始化，`init_fernet()` 显式调用）：

```python
_cipher = None  # 惰性，由 init_fernet() 初始化

def init_fernet():
    global _cipher
    if _cipher is not None:
        return
    key = os.getenv("MISS_FERNET_KEY", "")
    if key:
        _cipher = Fernet(key.encode())
    else:
        _cipher = Fernet(Fernet.generate_key())
```

然后在 `main.py` 的 `lifespan` 中调用 `init_fernet()`。桌面版依赖 `pythonengineservice.cs` 在启动时设置环境变量后调用。

#### Scenario: fernet.key 文件存在
- **WHEN** 桌面版启动
- **THEN** 读取 `fernet.key`，设为 `MISS_FERNET_KEY`，Python `init_fernet()` 使用持久密钥

#### Scenario: 首次启动
- **WHEN** `fernet.key` 不存在（首次启动）
- **THEN** 生成并持久化到文件，设环境变量

### Requirement: R01 — base_url SSRF 防护
The system SHALL 在 `config.py:apply_runtime_settings()` 中对 `openai_base_url` 进行格式校验：

```python
def _validate_base_url(url: str) -> str | None:
    if not url:
        return url
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"base_url scheme must be http or https: {parsed.scheme}")
    host = parsed.hostname or ""
    blocked = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
    if host in blocked:
        return ""  # 静默清除本地地址
    if any(host.startswith(p) for p in ("10.", "192.168.", "172.16.", "172.17.", "172.18.", "172.19.",
                                        "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
                                        "172.25.", "172.26.", "172.27.", "172.28.", "172.29.",
                                        "172.30.", "172.31.")):
        return ""  # 静默清除内网地址
    return url
```

#### Scenario: 正常 OpenAI URL
- **WHEN** 设置 `openai_base_url` 为 `https://api.openai.com/v1`
- **THEN** 校验通过

#### Scenario: 内网 SSRF URL
- **WHEN** 设置 `openai_base_url` 为 `http://192.168.1.1:8080`
- **THEN** 校验返回空字符串（静默清除）

#### Scenario: localhost URL
- **WHEN** 设置 `openai_base_url` 为 `http://127.0.0.1:11434/v1`（Ollama 本地）
- **THEN** 校验返回空字符串（本地 LLM 可通过设置 API Key 为 sk-placeholder 避免此限制）

### Requirement: R09 — requirements.txt 补充
The system SHALL 将 `instructor` 加入 `requirements.txt`：

```
instructor>=1.0.0
```

#### Scenario: pip install 后 instructor 可用
- **WHEN** 在新环境中执行 `pip install -r requirements.txt`
- **THEN** `from instructor import apatch, Mode` 成功

### Requirement: R11 — 日志参数化
The system SHALL 将 `memory_summarizer.py:L65`、`prompt_builder.py:L38`、`vector_store.py:L21` 的 f-string 日志改为 `%s` 参数化格式：

```python
# ❌ 改为前
logging.warning(f"[降级] vector_store.store 失败: {e}")
# ✅ 改为后
logging.warning("[降级] vector_store.store 失败: %s", e)
```

### Requirement: R12 — C# 日志转义
The system SHALL 在 `LoggingService.cs:Write()` 中对 `message` 进行换行符转义：

```csharp
var safeMessage = (message ?? "").Replace("\n", "\\n").Replace("\r", "\\r");
var line = $"{DateTime.Now:yyyy-MM-dd HH:mm:ss.fff} [{level}] {safeMessage}";
```
