# MISS Security Policy

> **项目**：MISS — Malleable Intelligent Synthetic Soul  
> **生效版本**：Beta v0.8  
> **最后更新**：2026-07-01  
> **安全等级**：A（38 项全修复 · 三专家联合签发）

---

## 一、适用范围

本策略适用于 MISS 项目的全部组件：

| 组件 | 语言 | 角色 |
|------|------|------|
| `miss-backend` | Python (FastAPI) | AI 引擎 + API 服务 |
| `miss-desktop-wpf` | C# (WPF) | 桌面客户端 |
| `miss-frontend-v2` | HTML/CSS/JS | 独立前端 |
| `build.ps1` | PowerShell | 打包脚本 |

## 二、漏洞报告机制

如果你在 MISS 中发现安全漏洞，请通过以下方式报告：

1. **GitHub Issues**：[New Issue](https://github.com/luyi14-bits/MISS-project/issues/new) — 打上 `security` 标签
2. **Email**：`luyi14-bits@users.noreply.github.com`（通过 GitHub noreply 中转发送）

### 响应时间承诺

| 严重程度 | 初始响应 | 修复时间 | 示例 |
|----------|----------|----------|------|
| 🔴 严重 | 24 小时内 | 72 小时内 | API Key 泄露、未授权访问 |
| 🟠 高危 | 48 小时内 | 1 周内 | 加密降级、CORS 绕过 |
| 🟡 中危 | 1 周内 | 下个版本 | SSRF、明文存储敏感字段 |
| 🟢 低危 / 🔵 建议 | 下个迭代 | 按优先级排期 | 日志注入、依赖版本 |

### 我们不会做的

- 对已公开的漏洞隐瞒不报
- 要求报告者签署 NDA 作为提交条件
- 对善意报告者采取法律行动

## 三、支持的版本

| 版本 | 安全支持 | 说明 |
|------|----------|------|
| Beta v0.8（当前） | ✅ 支持 | 当前活跃开发版本 |
| Alpha v0.3 - v0.7 | ❌ 停止支持 | 已被后续版本替代 |

## 四、安全架构

MISS 采用**纵深防御**模型，五层独立防护：

```
第 1 层：传输安全
├── C# 与 Python 之间为 pythonnet 单进程嵌入（无网络端口暴露）
├── 前端 API_BASE 仅绑定 127.0.0.1:8000
└── CORS ALLOWED_ORIGINS 严格白名单

第 2 层：认证鉴权
├── Bearer Token 中间件（AuthMiddleware）
├── PUBLIC_PATHS 白名单（/health /api/info /docs）
└── access_token 为空时自动 bypass（单用户模式）

第 3 层：应用安全
├── Pydantic Field 强制校验（max_length 4000）
├── slowapi 频率限制（10 req/min per endpoint）
├── 三级 API fallback（TOOLS → JSON → Raw）
└── 安全占位符（LLM 原文永不透传）

第 4 层：数据安全
├── Fernet AES-128-CBC 加密对话内容
├── LiteDB + PythonBridge.EncryptMessage 双保险
├── API Key 仅内存持有（_runtime_overrides）
└── SaveSettings 序列化前清除 openai_api_key

第 5 层：运维安全
├── build.ps1 4 阶段零泄漏打包
├── .env .db .pdb .instance 全覆盖清理
├── .gitignore 37 条排除规则
└── Stage 4 自动验证关键产物
```

完整架构见 [docs/安全技术文档.md](docs/安全技术文档.md)。

## 五、已知风险与已修复项

本项目的安全健康历史为 **5 阶段 38 项修复**，全部关闭。

| 阶段 | 日期 | 内容 | 修复项 |
|------|------|------|--------|
| 阶段 1 | 2026-06-26 | 基础设施（认证·密钥·堆栈·CORS·CSP·输入·限流） | S01-S04, S06-S07, S09-S10, S16 (11 项) |
| 阶段 2 | 2026-06-26 | 加密 + 限流 | S05, S08 (2 项) |
| 阶段 3 | 2026-06-28 | AI 生成代码审计 | S17-S21 (5 项) |
| 阶段 4 | 2026-06-28 | 可观测性加固 | F22-F26 (5 项) |
| 阶段 5 | 2026-06-28 | 去匿名化 | D1-D11 (11 项) |
| Git | 2026-06-28 | Git 仓库安全 | G1-G3 (2 已修复) |
| License | 2026-07-01 | 版权头合规（进行中） | — |

完整审计历史见 [docs/安全开发规范_审计报告与修复方案.md](docs/安全开发规范_审计报告与修复方案.md)。

## 六、安全开发流程

所有代码变更必须经过以下检查点：

### 6.1 编码阶段

- 新增端点：Pydantic Field 约束（`max_length` / `ge` / `le`）
- 新增异常处理：`logging.warning` 或 `logging.error`（禁止 `except: pass`）
- 新增 LLM 调用：走 `LLMCaller.call()` 三级 fallback（禁止直接调 SDK）
- 新增 JSON 解析：必须 catch `json.JSONDecodeError`
- 日志中不打印 API Key / Token / 消息内容
- 不返回 `_diag` / `traceback` / 内部路径

### 6.2 评审阶段

- [ ] 所有输入字段有 `Field(max_length=)` 约束
- [ ] 所有 except 有日志
- [ ] LLM 调用走封装层
- [ ] JSON 解析有异常处理
- [ ] 返回内容经过 `escapeHtml()` 或等效
- [ ] 非白名单路径有 Bearer Token 校验

### 6.3 发布前阶段

- [ ] `build.ps1` Stage 4 全绿
- [ ] `.pdb` `.env` `.db` `.instance` 零残留
- [ ] `dotnet build` 0 error
- [ ] `pytest` 190/190
- [ ] `git status` clean
- [ ] `git ls-files | grep "\.pdb\|\.exe\|\.db\|\.sqlite3"` 返回空

## 七、依赖管理

### 安全更新策略

- Python 依赖使用 `>=` 约束（`requirements.txt`），大版本更新需在 CI 中验证
- 发现 CVE 的依赖：P0，72 小时内更新
- 定期审计：每月执行 `pip list --outdated` 检查

### 当前关键依赖

| 包 | 最低版本 | 安全关键 |
|----|----------|----------|
| `cryptography` | 42.0.0 | ✅ Fernet 加密 |
| `fastapi` | 0.110.0 | ✅ API 框架 |
| `pydantic` | 2.0.0 | ✅ 输入校验 |
| `openai` | 1.30.0 | ✅ LLM 调用 |
| `slowapi` | 0.1.10 | ✅ 速率限制 |
| `sqlalchemy` | 2.0.0 | ✅ 数据库 |

## 八、许可证安全

- **项目许可证**：GNU AGPL v3
- **版权归属**：MISS Project Contributors
- **每个源文件头部**：必须包含 `SPDX-License-Identifier: AGPL-3.0-or-later`
- 第三方依赖的许可证兼容性已在 `requirements.txt` 中可追溯

SPDX 版权头规范见 [.trae/specs/fix-license-headers/spec.md](.trae/specs/fix-license-headers/spec.md)。

## 九、安全文档索引

| 文档 | 说明 |
|------|------|
| [安全技术文档](docs/安全技术文档.md) | 架构 · 威胁模型 · 模块详解 · 审计历史 |
| [安全审计报告](docs/安全开发规范_审计报告与修复方案.md) | 完整 5 阶段审计过程（70+ 页） |
| [Git 安全审计](miss-pipeline/git-security-audit.md) | G1-G3 仓库安全检查 |
| [LLM API 置信度审计](.trae/specs/fix-llm-api-compat/confidence-audit.md) | 三级 fallback 安全分析 |

---

> **安全顾问（SDL）**：安全不是一次性工程，是持续纪律。这份 Policy 是纪律的起点。  
> **安全顾问（Web 安全）**：如果你找到了没在这里列出的漏洞，请报告。我们不会让它留在已发布的版本里。  
> **安全顾问（二进制安全）**：你的代码跑在用户机器上。build.ps1 确保我们不会把 .pdb 和 .db 打包进去。基础工程做对了。
