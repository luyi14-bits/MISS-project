# MISS 项目管线看板

> 更新时间：2026-07-01 · 当前发布版本：Alpha v0.4

---

## 状态总览

| 状态 | Spec 数 | 说明 |
|------|---------|------|
| ✅ **已完成** | 10 | 已发布/验收通过 |
| 🔨 **开发中** | 0 | — |
| 📝 **规划中** | 1 | SillyTavern 角色卡兼容 |
| ❌ **废弃** | 1 | 技术方案变更（Tauri → pythonnet） |

---

## ✅ 已完成

### phase5-role-factory-tts — AI 角色工厂 + TTS 语音

> 精简方案：40 子任务 → 18 子任务，9 人天 → 4.5 人天

| Task | 内容 | 状态 |
|------|------|------|
| Task 1 | RoleData 新增 Id/Tags/CreatedAt/VoicePreset | ✅ |
| Task 2 | RoleFactory — 一次 instructor LLM 调用生成完整角色 | ✅ |
| Task 3 | KnowledgeDomainEngine — 领域标签前置注入 system prompt | ✅ |
| Task 4 | CreateRoleWindow "AI 一键生成"按钮 + 表单自动填充 | ✅ |
| Task 5 | EdgeTTSEngine + desktop_bridge.tts_speak() | ✅ |
| Task 6 | C# AudioPlayer (NAudio) + ConversationView 🔊 播放按钮 | ✅ |

**产物**：14 个文件已更改 +376/-29 · dotnet 0 error · pytest 190 passed

### fix-residual-risks — 加密体系对齐 + SSRF 防护

| Task | 内容 | 状态 |
|------|------|------|
| Task 1 | 记忆加密对齐 — memory_entries 读写全经过 encrypt/decrypt | ✅ |
| Task 2 | Fernet 密钥持久化 — fernet.key 文件 + crypto.py 惰性初始化 | ✅ |
| Task 3 | SSRF 防护 — _validate_base_url() 校验内网/localhost | ✅ |
| Task 4 | 辅助修复（日志参数化 + requirements.txt + C# 转义） | ✅ |

**安全效果**：安全等级 A · 38/38 全修复

### fix-license-headers — 全项目 SPDX 版权头补全

| Task | 内容 | 状态 |
|------|------|------|
| Task 1 | Python 文件 SPDX 头注入（排除 tests/data/） | ✅ |
| Task 2 | C# 文件 SPDX 头注入（排除 obj/） | ✅ |
| Task 3 | .gitignore *.PyInstaller.spec 修正 | ✅ |

**安全效果**：78 个源文件 100% 覆盖 SPDX-License-Identifier: AGPL-3.0-or-later

### fix-role-message-isolation — 角色切换消息隔离

| Task | 内容 | 状态 |
|------|------|------|
| Task 1 | 角色切换时消息隔离（OnCurrentRoleChanged Save→Clear→Load） | ✅ |
| Task 2 | session_id 嵌入角色名（pySessionId 已有 roleName） | ✅ |

**产物**：MainViewModel.cs OnCurrentRoleChanged 实现 Save→Clear→Load，含 try-catch + Trace.TraceError

### Git 安全审计 G1-G3

| Task | 内容 | 状态 |
|------|------|------|
| G1 | commit author 邮箱改为 noreply | ✅ |
| G2 | _wpftmp.csproj 移除 + .gitignore | ✅ |
| G3 | .docx/.doc 元数据移除 | ✅ |

### fix-llm-api-compat — 三级 API fallback

| Task | 内容 | 状态 |
|------|------|------|
| Task 1 | call() 改为三级 fallback（TOOLS→JSON→Raw） | ✅ |
| Task 2 | 推理模型检测 _is_reasoning_model() | ✅ |
| Task 3 | 安全占位符（不原文透传，防 system prompt 泄漏） | ✅ |

### fix-binding-and-api — 数据绑定断裂修复

| Task | 内容 | 状态 |
|------|------|------|
| Task 1 | 推理模型 instructor.Mode.JSON | ✅ |
| Task 2 | AttributePanel 10 硬编码 Slider 绑定 Profile | ✅ |
| Task 3 | ConversationView 标题栏角色感知 | ✅ |
| Task 4 | ⑨模式触发修复 | ✅ |
| Task 5 | API 配置持久化（LiteDB 双写） | ✅ |
| Task 6 | 侧边栏删除会话 | ✅ |

### desktop-polish — 全线打磨 21 项

| Task | 内容 | 状态 |
|------|------|------|
| Task 1 | 启动 Loading 窗口（异步初始化） | ✅ |
| Task 2 | 模态窗口 StaticResource → DynamicResource | ✅ |
| Task 3 | IO 线程隔离（File.ReadAllText → Task.Run） | ✅ |
| Task 4 | 4 处静默异常 → logging.warning | ✅ |
| Task 5 | config.py 字段去重 | ✅ |
| Task 6 | SliderItem → CommunityToolkit.Mvvm | ✅ |
| Task 7 | MessageBox → NotificationService | ✅ |

### desktop-rebuild — WPF MVVM + pythonnet + LiteDB

| Task | 内容 | 状态 |
|------|------|------|
| Task 0 | MainViewModel MVVM 核心 | ✅ |
| Task 1-2 | SessionData + 侧边栏改造 | ✅ |
| Task 3 | ConversationView + 上下文截断 + instructor 化 | ✅ |
| Task 4-5 | ⑨主题联动 + 内心独白开关 | ✅ |
| Task 6-8 | 属性面板折叠 + LiteDB + 标题栏 | ✅ |

### 安全审计 5 阶段 — 38/38 全部修复

| 阶段 | 修复项 | 状态 |
|------|--------|------|
| 阶段 1 | 认证/脱敏/CORS/限流/CSP/输入校验/Settings | ✅ |
| 阶段 2 | 加密存储/频率限制 | ✅ |
| 阶段 3 | 双存储加密空洞/异常泄漏/Key落盘/流式透传/_error格式 | ✅ |
| 阶段 4 | placeholder检查/日志/SSE解析/crypto精确化/FERNET_KEY告警 | ✅ |
| 阶段 5 | 去匿名化（.pdb/.env/.db/.instance 清理 + 目录删除 + .gitignore 加固） | ✅ |

**安全等级**：A（10🔴修复 + 12🟠修复 + 11🟡修复 + 3🟢修复 + 2🔵建议）

---

## 📝 规划中

### sillytavern-card-compat — SillyTavern 角色卡兼容

| Task | 内容 | 状态 |
|------|------|------|
| Task 1 | TavernCardParser — PNG tEXt "ccv3" chunk 解析 | 📝 |
| Task 2 | TavernCardExporter — RoleData → ST 角色卡 PNG | 📝 |
| Task 3 | RoleData 新增 6 个 ST 兼容字段 | 📝 |
| Task 4 | CreateRoleWindow "📥 导入 ST 角色卡" 按钮 | 📝 |
| Task 5 | RoleSidebar "🎴 导出 ST 角色卡" 按钮 | 📝 |

### 远景 — 后续规划

| 项目 | 内容 | 优先级 |
|------|------|--------|
| C# 单元测试基础设施 | xUnit/NUnit 零 → 补覆盖 | P2 |
| 头像生成 | DALL·E 可选按钮 + Character Card PNG | P3 |

---

## ❌ 废弃

### desktop-packaging — Tauri 桌面版

**废弃原因**：技术方案已从 Tauri（双进程 HTTP）变更为 WPF + pythonnet（单进程嵌入）。Tauri 分支不再维护。

---

## 发布历史

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-07-01 | Alpha v0.4 | Phase 5+6 上线（角色工厂+领域约束+TTS）+ 残余风险修复 + 版权头补全 |
| 2026-06-28 | v0.3.0-alpha | 三级 API fallback + 安全审计 5 阶段 + 去匿名化 |
| 2026-06-27 | — | MVVM 重构 + LiteDB + 绑定修复 |
| 2026-06-26 | — | pythonnet 桥接 + 安全审计 4 阶段 |
| 2026-06-25 | — | 角色创建保存 + UI 修复 + 初始提交 |

---

## 阻塞项

**无阻塞项。** 当前版本（Alpha v0.4）：

```
dotnet build: 0 error
pytest:       ~190 passed
安全审计:     A (38/38)
Spec PASS:    10/11（fix-role-message-isolation ✅ · sillytavern-card-compat 📝 规划中）
CLA:          已发布（提交即同意模式）
```
