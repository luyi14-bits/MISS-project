# MISS 项目管线看板

> 更新时间：2026-07-09 · 当前发布版本：Beta v0.6 · 阶段：Beta 推进中

---

## 状态总览

| 状态 | Spec 数 | 说明 |
|------|---------|------|
| ✅ **已完成** | 13 | 已发布/验收通过 |
| 🔨 **开发中** | 1 | 插件系统 (Plugin System) |
| 📝 **规划中** | 2 | 远期愿景 |
| 💡 **想法池** | 5 | 待 RICE 评审 |
| ❌ **废弃** | 1 | 技术方案变更（Tauri → pythonnet） |

---

## ✅ 已完成

### v0.6 新增（3 次提交，4 个 Spec 交付）

| Spec | 内容 | 日期 |
|------|------|------|
| sillytavern-card-compat | TavernCardParser/Exporter + 导入导出 UI（5 Tasks） | 07-08 |
| 对话导出 | ConversationExporter — JSON/HTML/Markdown 三格式 | 07-09 |
| 语音输入 STT | AudioRecorder + WhisperSttService + 🎤 Push-to-Talk | 07-09 |
| xUnit 测试 | miss-desktop-wpf.Tests 项目，CoreDomainTests 9/9 PASS | 07-09 |

### v0.6 新增文件（666 行 C#）

| 文件 | 行数 | 功能 |
|------|------|------|
| `TavernCardParser.cs` | 161 | PNG tEXt ccv3 chunk → TavernCardV3 模型 |
| `TavernCardExporter.cs` | 144 | RoleData → ST V3 card PNG (CRC-32) |
| `ConversationExporter.cs` | 136 | 对话导出 JSON/HTML/Markdown |
| `AudioRecorder.cs` | 108 | NAudio 麦克风 → 16kHz WAV |
| `WhisperSttService.cs` | 92 | Whisper.net ggml-tiny 离线转写 |
| `CoreDomainTests.cs` | 128 | xUnit 9 tests (9/9 PASS) |

### v0.5 交付

| Spec | 内容 |
|------|------|
| fix-role-message-isolation | 角色切换消息隔离 Loop #1 |
| pm-mentor | 产品经理 Skill（PRD/RICE/路线图） |
| 标准文件 8/8 | CONTRIBUTING/CODE_OF_CONDUCT/CHANGELOG/.github/ |

### 历史 Spec（v0.4 及之前）

| Spec | 内容 |
|------|------|
| phase5-role-factory-tts | AI 角色工厂 + TTS（40→18 精简） |
| fix-residual-risks | 加密对齐 + Fernet + SSRF |
| fix-license-headers | 78 源文件 SPDX |
| 安全审计 5 阶段 | 38/38 · A 级 |
| fix-llm-api-compat | 三级 API fallback |
| fix-binding-and-api | 6 Tasks |
| desktop-polish | 21 项 |
| desktop-rebuild | MVVM+pythonnet+LiteDB |
| fix-role-save-and-ui | 角色创建 + UI |
| Phase 0-7 | 核心引擎 |

---

## 💡 想法池

| 想法 | 描述 | 估时 | 价值 |
|------|------|------|------|
| **多语言 UI 支持** | WPF 界面英/中/日可切换，接入 resx 本地化 | 1.5d | 🟡 中 |
| **角色进阶系统** | 对话中属性渐变，完成度可视化 | 3d | 🟡 中 |
| **插件系统** | Python sidecar 接口，第三方自定义行为/表情/动画 | 5d | 🟢 高 |
| **WebUI 模式** | 可选启动 Web 前端（React/Vue），脱离 WPF 桌面 | 3d | 🟡 中 |
| **移动端适配** | MAUI / React Native 移动客户端 | 8d | 🟢 高 |
| **多人角色房间** | 多角色同时对话，角色间互动 | 4d | 🟡 中 |

---

## 🧠 Skill 清单

| Skill | 用途 | 来源 |
|-------|------|------|
| `project-secretary` | 项目秘书：文件/Git/看板/Skill管理/留痕 | MISS |
| `spec-pipeline` | 管线工程师：Spec/任务拆分/置信度审计 | MISS |
| `pm-mentor` | 产品经理：PRD/RICE/路线图/竞品分析 | deanpeters/spec-kit |
| `loop-sop` | 开发循环调度：五阶段门禁/降级/迭代追踪 | MISS + WeChatAuto |
| `coding-ethics` | 编程八荣八耻：14 条红线 + 打包清单 | MISS |
| `acceptance-testing` | 严格验收：三层覆盖 + 陷阱清单 + Spec审计 | MISS |
| `security-academy` | 安全学院：Miessler/Kettle/Ormandy 三轮 | MISS |
| `test-driven-development` | 测试铁三角：Beck/Stewart/Okken | MISS |
| `trinity-mentors` | AI导师团：Raschka/Karpathy/Lyalin | 通用 |
| `horror-story-writer` | 恐怖短篇写手：故事会风格 + 2025爆款技法 | 阴阳先生手记 |

## ❌ 废弃

### desktop-packaging — Tauri 桌面版

**废弃原因**：技术方案已从 Tauri（双进程 HTTP）变更为 WPF + pythonnet（单进程嵌入）。

---

## 发布历史

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-07-09 | Beta v0.6 | ST 角色卡 + Whisper STT + 对话导出 + xUnit 9/9 |
| 2026-07-08 | Beta v0.5 | 🏁 Alpha→Beta · 全部 Spec PASS · 标准文件 8/8 |
| 2026-07-01 | Alpha v0.4 | Phase 5+6 上线（角色工厂+TTS）+ 残余风险修复 |
| 2026-06-28 | v0.3.0-alpha | 三级 fallback + 安全审计 5 阶段 |

---

## 阻塞项

**无阻塞项。** 当前版本（Beta v0.6）：

```
dotnet build:   0 error
pytest:         ~190 passed
xUnit:           9/9  PASS
安全审计:       A (38/38)
Spec PASS:      10/10 + 3 v0.6 Specs
Skills:         10 个
标准文件:        8/8 齐全
Git Tag:        v0.6.0-beta ✅
```
