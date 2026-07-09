# MISS 项目标准操作程序 (SOP)

> **版本**: v1.0 · **适用**: Beta v0.6+ · **最后更新**: 2026-07-10

---

## 1. 项目概览

**MISS**（Malleable Intelligent Synthetic Soul）是一个以双轨思维引擎驱动的 AI 角色对话框架。全栈 Python + Jinja2 + FastAPI 后端，WPF（C#/.NET）+ pythonnet 单进程嵌入桌面客户端，独立 HTML/CSS/JS 前端。AGPL v3 开源。

| 指标 | 当前值 |
|------|--------|
| pytest | ~190/190 PASS |
| xUnit | 9/9 PASS |
| Spec | 13 个全部 PASS |
| 安全等级 | A（38/38 修复） |
| 当前版本 | Beta v0.6 |

---

## 2. 技术栈与项目结构

```
MISS/
├── miss-backend/           # FastAPI + SQLAlchemy + ChromaDB（Python）
│   ├── models/             # ORM: session, message, memory, preset
│   ├── services/           # 12 个业务模块（属性引擎/提示词/LLM/记忆/TTS/角色工厂）
│   ├── routers/            # 6 个 API 端点模块
│   ├── middleware/         # Bearer Token 鉴权
│   ├── templates/          # Jinja2 系统提示词 miss_system.j2
│   ├── frontend/           # Web 版前端
│   ├── frontend-desktop/   # 桌面版前端
│   └── tests/              # pytest 测试套件（13 个文件）
├── miss-desktop-wpf/       # WPF MVVM 桌面客户端（C#）
│   ├── Services/           # 8+ C# 服务（PythonBridge/AudioRecorder/WhisperSTT/…）
│   ├── ViewModels/         # CommunityToolkit.Mvvm
│   ├── Views/              # XAML 视图
│   └── miss-desktop-wpf.Tests/  # xUnit 测试
├── miss-frontend-v2/       # 独立前端设计稿
├── miss-pipeline/          # 管线看板（HTML Kanban + ECharts）
├── docs/                   # 技术文档（5 份）
├── avatars/                # 14 个角色头像
├── 验收报告/               # 18 份验收报告 + 问题追踪
├── .trae/
│   ├── specs/              # 13 个 Spec（每个含 spec.md + tasks.md + checklist.md）
│   └── skills/             # 8 个团队角色 Skill
└── .github/                # ISSUE_TEMPLATE + PULL_REQUEST_TEMPLATE + CODEOWNERS
```

---

## 3. 开发工作流（Spec-Driven Pipeline）

```
产品需求 → Spec 编写 → 任务拆分 → 实现 → 验收 → 发布
```

### 3.1 Spec 编写（管线工程师）

1. 在 `.trae/specs/<spec-name>/` 下创建三个文件：
   - `spec.md` — 含 Why / Meta（优先级+工时）/ What Changes / Impact / ADDED-MODIFIED-REMOVED Requirements
   - `tasks.md` — 可独立实现的任务清单，每个任务含目标/输入输出/依赖/验收标准
   - `checklist.md` — 逐项勾选的验收清单
2. 标记优先级：**P0**（阻塞）→ **P1**（体验）→ **P2**（质量）→ **P3**（远期）
3. 高风险的架构变更须额外创建 `confidence-audit.md`
4. 同步更新 `miss-pipeline/PIPELINE_KANBAN.md`

### 3.2 编码实现（修复工程师）

1. **始终遵守** `.trae/skills/coding-ethics/SKILL.md`（编程八荣八耻）：
   - 每新增公开类/函数，同步在 `__init__.py` 中导出
   - 所有数据库操作必须有 `try/except/rollback/finally: close()`
   - 使用 Pydantic `BaseSettings` + `SettingsConfigDict(env_file=".env")`，不要手工 `load_dotenv()` + `os.getenv()`
   - 不写 SQLite 专有 SQL；使用 SQLAlchemy 抽象
   - 魔法数字命名常量，业务逻辑不硬编码
   - 正则/边界条件写测试覆盖
   - 前后端接口用 Pydantic model 定义契约
   - WPF UI 线程通过 `Dispatcher.InvokeAsync`，后台任务用 `Task.Run`
2. 每个任务完成后运行：
   - `pytest -q`（后端）
   - `dotnet build -c Release`（桌面端）
   - `dotnet test`（C# 测试）

### 3.3 验收测试（验收人）

**铁律：永远不信任修复工程师的声明。**

| 修复组声明 | 验收人动作 |
|-----------|-----------|
| "pytest 190/190" | 自己跑 `pytest -q` |
| "dotnet build 0 error" | 自己跑 `dotnet build -c Release` |
| "启动正常" | 自己 `dotnet publish` → 双击 `MISS.exe` |
| "加密了" | 自己读 `SaveSettings` 函数 |

验收人三件事：
1. **逐文件读回** — 独立打开修改的文件，逐行对照
2. **实测执行** — 运行构建/测试/启动
3. **证据可视化** — PASS/FAIL 附 `file:///` 绝对路径 + 行号

问题严重度：🔴 严重 → 🟠 高危 → 🟡 中危 → 🟢 低危 → 🔵 建议

---

## 4. 分支与提交规范

```
main                          # 主线（每个 Beta 版本一个 tag）
├── feature/<spec-name>       # 功能分支
├── fix/<issue-id>            # 修复分支
└── release/v<version>        # 发布分支
```

- **Commit message**: `<type>: <简短描述>`
  - `feat:` 新功能
  - `fix:` 修复
  - `docs:` 文档
  - `test:` 测试
  - `refactor:` 重构
  - `chore:` 杂项
- 每个功能/修复完成后 squash merge 回 main
- 发布时打 tag：`v0.6.0-beta`

---

## 5. 测试标准

| 层级 | 框架 | 负责人 | 要求 |
|------|------|--------|------|
| 单元测试 | pytest | 后端开发 | 每个 service 函数必须有对应 test |
| 单元测试 | xUnit | C# 开发 | 核心域模型必须覆盖 |
| 集成测试 | pytest | 后端开发 | 每个 API 端点至少 1 个集成测试 |
| E2E | 手动 | 验收人 | 关键路径 3-5 条，dotnet publish 后启动验证 |

**测试运行命令：**
```bash
# 后端
cd miss-backend && python -m pytest -q

# 桌面端
cd miss-desktop-wpf && dotnet test
```

---

## 6. 安全红线

从 `SECURITY.md` 和 `docs/安全开发规范_审计报告与修复方案.md` 提取：

| # | 红线 | 检查点 |
|---|------|--------|
| 1 | API Key 绝不存储于 localStorage/明文/日志 | `SaveSettings` 序列化前清除 Key |
| 2 | 全 API 必须经过 `AuthMiddleware` | `PUBLIC_PATHS` 白名单外一律鉴权 |
| 3 | 数据库操作必须加密后落盘 | Fernet + LiteDB 双重加密 |
| 4 | 输入强制长度校验 | Pydantic `max_length=4000` |
| 5 | 请求频率限制 | slowapi 10 req/min per endpoint |
| 6 | CORS 白名单 | `ALLOWED_ORIGINS` 严格限定 |
| 7 | 诊断信息不暴露堆栈 | `_diag` 字段禁止返回内部路径 |
| 8 | SQL 参数化查询 | 禁止字符串拼接 SQL |

---

## 7. 发布流程

1. **冻结代码** — main 分支锁定，只接受 bugfix
2. **全量测试** — `pytest -q`（~190）+ `dotnet test`（9）+ `dotnet build -c Release`
3. **验收通过** — 对应 Spec 的 `checklist.md` 全部勾选
4. **更新文档** — `CHANGELOG.md` + `PIPELINE_KANBAN.md` + `README.md` 状态声明
5. **打 Tag** — `git tag -a vX.Y.Z-beta -m "Beta vX.Y"`
6. **发布** — GitHub Release + 发布说明

---

## 8. 常用命令速查

```bash
# === 后端 ===
cd miss-backend
pip install -r requirements.txt
cp .env.example .env          # 编辑填入 OPENAI_API_KEY
python -m uvicorn main:app --host 127.0.0.1 --port 8000
python -m pytest -q           # 跑测试

# === 桌面端 ===
cd miss-desktop-wpf/build
.\build.ps1                   # 安装嵌入版 Python 3.12 + 依赖
cd ..
dotnet build -c Release
dotnet run
dotnet test                   # 跑 xUnit

# === 打包发布 ===
cd miss-desktop-wpf
dotnet publish -c Release -o publish
```

---

## 9. 团队角色（8 个 AI Skill）

| Skill | 角色 | 职责 |
|-------|------|------|
| `pm-mentor` | 产品经理 | PRD/优先级/路线图 |
| `spec-pipeline` | 管线工程师 | Spec 编写/任务拆分/看板维护 |
| `coding-ethics` | 编码规范 | 八荣八耻强制执行 |
| `test-driven-development` | 测试方法论 | TDD + pytest + E2E |
| `acceptance-testing` | 验收测试 | 独立验收/证据驱动/严重度分级 |
| `security-academy` | 安全专家 | STRIDE + 5 层防御 + 审计 |
| `project-secretary` | 项目秘书 | 文件整理/管线维护/标准审计 |
| `trinity-mentors` | AI/ML 导师团 | 算法/架构咨询 |

---

## 10. 紧急联系人

- 安全漏洞：GitHub Issues 打 `security` 标签，或 `luyi14-bits@users.noreply.github.com`
- 严重漏洞响应：24h 内 / 修复：72h 内
- 高危漏洞响应：48h 内 / 修复：1 周内

---

> 以上 SOP 基于当前项目文件（README、CHANGELOG、PIPELINE_KANBAN、SECURITY、各 Skill、验收文档、安全审计报告）整理。随项目演进持续更新。
