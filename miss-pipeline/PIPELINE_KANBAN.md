# MISS 项目管线看板

> 更新时间：2026-07-08 · 当前发布版本：Beta v0.5 · 阶段：Beta 封板

---

## 状态总览

| 状态 | Spec 数 | 说明 |
|------|---------|------|
| ✅ **已完成** | 11 | 已发布/验收通过 |
| 📝 **规划中** | 3 | Beta 阶段目标 + 远期愿景 |
| 💡 **想法池** | 8 | 待评估/待讨论 |
| ❌ **废弃** | 1 | 技术方案变更（Tauri → pythonnet） |

---

## ✅ 已完成

### fix-role-message-isolation — 角色切换消息隔离

> Loop #1 已交付 — Bug A（前端 Filter）+ Bug B（session_id 含角色名）

| Task | 内容 | 状态 |
|------|------|------|
| Task 1 | 角色切换时消息隔离（save→clear→load filtered） | ✅ |
| Task 2 | session_id 加角色名（Python 侧零改动） | ✅ |

### pm-mentor — 产品经理 Skill 🆕

> 基于 deanpeters/Product-Manager-Skills（4.5k stars）+ github/spec-kit

| 能力 | 工具 |
|------|------|
| PRD 写作 | 12 段标准化模板（Executive Summary → Open Questions） |
| 优先级排序 | RICE / ICE / MoSCoW 框架 |
| 路线图规划 | Now-Next-Later（Bruce McCarthy 方法论） |
| 竞品分析 | 横向对比表模板 |

### 标准文件补齐（对标 100k Star+ 仓库）

| 文件 | 状态 |
|------|------|
| CONTRIBUTING.md / CODE_OF_CONDUCT.md / CHANGELOG.md | ✅ 新增 |
| .github/CODEOWNERS | ✅ 新增 |
| .github/ISSUE_TEMPLATE/ (bug_report + feature_request) | ✅ 新增 |
| .github/PULL_REQUEST_TEMPLATE.md | ✅ 新增 |

根目录标准文件：**8/8 齐全**（README / LICENSE / SECURITY / CLA / CONTRIBUTING / CODE_OF_CONDUCT / CHANGELOG / .gitignore）

### phase5-role-factory-tts — AI 角色工厂 + TTS 语音

> 精简方案：40 子任务 → 18 子任务，9 人天 → 4.5 人天

| Task | 内容 | 状态 |
|------|------|------|
| Task 1 | RoleData 新增 Id/Tags/CreatedAt/VoicePreset | ✅ |
| Task 2 | RoleFactory — 一次 instructor LLM 调用生成完整角色 | ✅ |
| Task 3 | KnowledgeDomainEngine + KnowledgeFilter.log_only() | ✅ |
| Task 4 | CreateRoleWindow "AI 一键生成" | ✅ |
| Task 5-6 | EdgeTTSEngine + AudioPlayer (NAudio) + ConversationView 🔊 | ✅ |
| P5-001/002/003 | KnowledgeDomain 修复（log_only + __all__ + edge-tts 安装） | ✅ |

### fix-residual-risks — 加密体系对齐 + SSRF 防护

| Task | 内容 | 状态 |
|------|------|------|
| Task 1-4 | 记忆加密对齐 + Fernet 持久化 + SSRF + 辅助修复 | ✅ |

### fix-license-headers — 全项目 SPDX 版权头补全

| Task | 内容 | 状态 |
|------|------|------|
| Task 1-3 | Python + C# 78 源文件 SPDX + .gitignore 修正 | ✅ |

### sillytavern-card-compat — SillyTavern 角色卡兼容

| Task | 内容 | 状态 |
|------|------|------|
| Task 1 | TavernCardParser — PNG tEXt "ccv3" chunk 解析 | ✅ |
| Task 2 | TavernCardExporter — RoleData → ST 角色卡 PNG | ✅ |
| Task 3 | RoleData 新增 6 个 ST 兼容字段 | ✅ |
| Task 4 | CreateRoleWindow "📥 导入 ST 角色卡" 按钮 | ✅ |
| Task 5 | RoleSidebar "🎴 导出 ST 角色卡" 按钮 | ✅ |

**产物**：6 个新文件/修改文件 · 零外部依赖 · ST V3 格式兼容

### 其余已发布 Spec

| Spec | 内容 |
|------|------|
| fix-llm-api-compat | 三级 API fallback（TOOLS→JSON→Raw） |
| fix-binding-and-api | 数据绑定断裂修复（6 Tasks） |
| desktop-polish | 全线 21 项打磨 |
| desktop-rebuild | WPF MVVM + pythonnet + LiteDB |
| fix-role-save-and-ui | 角色创建保存 + UI 修复 |

### 安全审计 5 阶段 — 38/38 全部修复

| 阶段 | 修复项 | 状态 |
|------|--------|------|
| 阶段 1-5 | 认证/加密/限流/CSP/CORS/去匿名化/打包加固 | ✅ |
| 安全等级 | **A**（10🔴修复 + 12🟠修复 + 11🟡修复 + 3🟢修复 + 2🔵建议） | ✅ |

---

## 📝 规划中

### v1.0 — Beta 阶段目标

| 项目 | 内容 | 优先级 |
|------|------|--------|
| C# 单元测试基础设施 | xUnit 零 → 补覆盖 | P2 |
| 社区反馈迭代 | 根据实际使用反馈修 bug + 优化 | P1 |

### v2.0 远期

| 项目 | 内容 | 优先级 |
|------|------|--------|
| 全功能 MCP Server | 标准化 AI 接口 | 💡 |
| 社区预设市场 | 用户分享角色预设 | 💡 |

---

## 💡 想法池

| 想法 | 描述 | 估时 | 价值 |
|------|------|------|------|
| **多语言 UI 支持** | WPF 界面英/中/日可切换，接入 resx 本地化 | 1.5d | 🟡 中 |
| **对话导出（JSON/HTML/PDF）** | 导出角色 + 对话历史，可分享/打印 | 1d | 🟢 高 |
| **角色进阶系统** | 对话中属性渐变（如好感度+1每次聊天），完成度可视化 | 3d | 🟡 中 |
| **插件系统** | Python sidecar 插件接口，第三方自定义行为/表情/动画 | 5d | 🟢 高 |
| **WebUI 模式** | 可选启动 Web 前端（React/Vue），脱离 WPF 桌面 | 3d | 🟡 中 |
| **移动端适配** | MAUI / React Native 移动客户端，同步桌面数据 | 8d | 🟢 高 |
| **多人角色房间** | 多角色同时对话，角色间有互动和反应 | 4d | 🟡 中 |
| **语音输入 STT** | Whisper 本地语音转文字 → 对话输入，完全离线 | 2d | 🟡 中 |

> 想法池项目均为未评估/未排期的创意。优先级由 PM Mentor（`pm-mentor` Skill）在未来 RICE 评审中决定。

---

## ❌ 废弃

### desktop-packaging — Tauri 桌面版

**废弃原因**：技术方案已从 Tauri（双进程 HTTP）变更为 WPF + pythonnet（单进程嵌入）。

---

## 发布历史

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-07-08 | Beta v0.5 | 🏁 Alpha 封板 → Beta 正式开启 · 全部 Spec PASS · 标准文件 8/8 |
| 2026-07-01 | Alpha v0.4 | Phase 5+6 上线（角色工厂+领域约束+TTS）+ 残余风险修复 |
| 2026-06-28 | v0.3.0-alpha | 三级 API fallback + 安全审计 5 阶段 + 去匿名化 |

---

## 阻塞项

**无阻塞项。** 当前版本（Beta v0.5）已封板：

```
dotnet build:   0 error
pytest:         ~190 passed
安全审计:       A (38/38)
Spec PASS:      10/10（全部通过）
Skills:          8 个（全部 v3）
标准文件:        8/8 齐全
Git Tag:        v0.5.0-beta ✅
```
