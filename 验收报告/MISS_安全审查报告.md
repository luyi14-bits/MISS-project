# MISS 安全审查报告

> 审计范围：`miss-backend/` + `miss-desktop-pywv/` | 审计日期：2026-06-26 | 审计人：严格验收 Agent

---

## 一、审计摘要

| 项 | 结果 |
|----|------|
| 审计条目 | 7 |
| 🔴 高风险 | 1 |
| 🟡 中风险 | 1 |
| 🟢 低风险 / 已修复 | 5 |
| 总体评级 | ⚠️ B+（发布前解决 1 个高风险项后可到 A） |

---

## 二、详细发现

### 🔴 SEC-001：PyInstaller 打包 `console=True` 导致控制台窗口暴露

| 属性 | 值 |
|------|-----|
| **严重度** | 🔴 高 |
| **影响范围** | `miss-desktop-pywv/build/MISS/MISS.exe` |
| **所在文件** | [MISS.spec L41](file:///d:/Desktop/MISS/miss-desktop-pywv/MISS.spec#L41) |
| **发现日期** | 2026-06-26 |
| **状态** | ⏳ 待修复 |

**问题描述**：

PyInstaller 打包配置中 `console=True`，导致用户双击 `MISS.exe` 时会弹出一个**控制台黑框窗口**伴随应用窗口同时显示。

**安全影响**：

1. **敏感信息泄漏**：FastAPI / uvicorn 的 stdout/stderr 会直接打印到控制台。如果代码中有 `print(api_key)` 或第三方库在异常信息中携带请求参数（如 OpenAI SDK 报错时可能打印请求 body），用户的 API key 会明文暴露在控制台窗口中。

2. **攻击面扩大**：控制台窗口可被其他进程读取 stdout 管道，理论上可被恶意软件截获输出内容。

3. **用户体验降级**：普通用户看到控制台黑框会认为程序崩溃或"不正规"。

**影响链路**：

```
用户双击 MISS.exe
  → 控制台窗口弹出（黑框）
    → uvicorn 启动日志打印到控制台
    → 若 API 调用异常:
        → OpenAI SDK traceback 可能含请求参数
        → 若请求参数含 api_key:
            → 用户 API key 明文暴露在控制台
```

**修复方案**：

```python
# MISS.spec L41 — 将
console=True,
# 改为
console=False,
```

或在 PyInstaller 命令行添加 `--windowed`（与 implementation.md L203 中已记录的命令一致）。

**验证方法**：修复后重新打包，双击 `MISS.exe` 应仅弹出原生应用窗口，无控制台黑框。

---

### 🟡 SEC-002：CSP 历史曾含 `unsafe-inline`（v2 已修复）

| 属性 | 值 |
|------|-----|
| **严重度** | 🟡 中 → ✅ 已修复 |
| **影响范围** | Tauri 桌面版前端 |
| **所在文件** | [tauri.conf.json L21](file:///d:/Desktop/MISS/miss-desktop/src-tauri/tauri.conf.json#L21) |
| **状态** | ✅ 已修复（v2 重构） |

**修复前**（v1）：
```json
"csp": "default-src 'self' http://127.0.0.1:8000; script-src 'self' 'unsafe-inline' ..."
```

**修复后**（v2）：
```json
"csp": "default-src 'self'; script-src 'self' ..."
```

`unsafe-inline` 已移除，所有事件绑定改为 `addEventListener`。

---

### 🟢 SEC-003：AuthMiddleware — Bearer Token 鉴权 ✅

| 属性 | 值 |
|------|-----|
| **严重度** | 🟢 无风险 |
| **所在文件** | [middleware/auth.py](file:///d:/Desktop/MISS/miss-backend/middleware/auth.py) |

**评估**：

- 默认不启用（`config.access_token` 为空或 `"change-me-in-production"` 时不生效）
- 公开路径白名单正确（`/health`, `/api/info`, `/docs`, `/redoc`, `/openapi.json`, `/favicon.ico`）
- 启用后要求 `Authorization: Bearer <token>`，token 不匹配返回 401
- 部署建议：生产环境务必设置强随机 token

---

### 🟢 SEC-004：crypto.py — API Key Fernet 加密存储 ✅

| 属性 | 值 |
|------|-----|
| **严重度** | 🟢 无风险 |
| **所在文件** | [services/crypto.py](file:///d:/Desktop/MISS/miss-backend/services/crypto.py) |

**评估**：

- 使用 `cryptography.fernet`（基于 AES-128-CBC + HMAC-SHA256，行业标准）
- 密钥来源：环境变量 `MISS_FERNET_KEY`，未设置则自动生成（进程级随机密钥）
- 向后兼容 `PLAIN:` 前缀遗留明文
- 部署建议：生产环境务必通过环境变量注入固定 `MISS_FERNET_KEY`，否则重启后密钥变化导致已加密数据无法解密

---

### 🟢 SEC-005：slowapi 速率限制 ✅

| 属性 | 值 |
|------|-----|
| **严重度** | 🟢 无风险 |
| **所在文件** | [main.py L22-L23](file:///d:/Desktop/MISS/miss-backend/main.py#L22-L23) + 各路由 |

**评估**：

- `/api/chat`：`10/minute`（防滥用）
- `/api/character/analyze`：`5/minute`（防 LLM API 费用攻击）
- `/api/settings` POST：`5/minute`（防暴力修改）
- 429 响应干净：`{"detail": "请求过于频繁，请稍后再试"}`（不泄漏内部信息）
- 基于客户端 IP 限流（`get_remote_address`），对桌面应用足够

---

### 🟢 SEC-006：CORS 中间件 ✅

| 属性 | 值 |
|------|-----|
| **严重度** | 🟢 无风险 |
| **所在文件** | [main.py L51-L57](file:///d:/Desktop/MISS/miss-backend/main.py#L51-L57) |

**评估**：

- 仅允许白名单来源：`127.0.0.1:8000`, `localhost:8000`, `127.0.0.1:1420`, `tauri://localhost`
- **不允许通配符 `*`** — 正确
- 仅允许必要方法：`GET`, `POST`, `DELETE`, `OPTIONS`
- 仅允许必要请求头：`Authorization`, `Content-Type`

---

### 🟢 SEC-007：ChatRequest 输入校验 ✅

| 属性 | 值 |
|------|-----|
| **严重度** | 🟢 无风险 |
| **所在文件** | [routers/chat.py L16-L20](file:///d:/Desktop/MISS/miss-backend/routers/chat.py#L16-L20) |

**评估**：

- `session_id`：`max_length=64`（防超长字符串攻击）
- `message`：`min_length=1, max_length=4000`（防空消息 + 防 token 消耗攻击）
- `background`：`max_length=2000`

---

## 三、修复优先级

| 优先级 | ID | 修复项 | 预计工作量 |
|--------|----|--------|-----------|
| 🔴 P0 | SEC-001 | `console=True` → `console=False` | 1 行改动 + 重新打包 |
| 🟡 P1 | — | 生产环境强制设置 `MISS_FERNET_KEY` + `access_token` | 运维配置 |

---

## 四、未发现的安全问题

以下项目已审查，**未发现安全风险**：

- ✅ 敏感信息不写入日志（`logging.basicConfig(level=INFO)`，无 `print(api_key)`）
- ✅ API key 在 GET `/api/settings` 返回中以 `***` 脱敏
- ✅ `settings.py` 中 POST body 不包含 api_key 明文回显
- ✅ 预设导出/导入使用 JSON 格式，不执行代码
- ✅ 无 `eval()` / `exec()` 使用
- ✅ 无 SQL 注入风险（全部使用 SQLAlchemy ORM 参数化查询）
- ✅ 无路径遍历风险（StaticFiles 由 Starlette 内置保护）

---

*报告生成时间：2026-06-26*
*下次审计触发条件：SEC-001 修复后 / 发布前*
