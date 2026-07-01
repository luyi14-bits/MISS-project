# MISS 项目管线看板

> 更新时间：2026-07-01 · 当前发布版本：Beta v0.8

---

## 状态总览

| 状态 | Spec 数 | 说明 |
|------|---------|------|
| ✅ **已完成** | 8 | 已发布/验收通过 |
| 🔄 **进行中** | 1 | License 头部规范化 |
| 📝 **规划中** | 2 | Phase 5/6 + 加密体系对齐 + SSRF 防护 |
| ❌ **废弃** | 1 | 技术方案变更（Tauri → pythonnet） |

---

## ✅ 已完成

### fix-role-message-isolation — 角色切换消息隔离

| Task | 内容 | 状态 |
|------|------|------|
| Task 1 | 角色切换时消息隔离（save→clear→load filtered） | ✅ |
| Task 2 | session_id 加角色名 | ✅ |

**产物**：8/8 diff · Filter+pySessionId · 角色隔离+FULL PASS

### Git 安全审计 G1-G3

| Task | 内容 | 状态 |
|------|------|------|
| G1 | commit author 邮箱改为 noreply | ✅ |
| G2 | _wpftmp.csproj 移除 + .gitignore | ✅ |
| G3 | .docx/.doc 元数据移除 | ✅ |
| 发布 | 所有阶段 5 修改推送至远程 | ✅ |

### desktop-rebuild — MVVM + pythonnet + LiteDB + instructor

| Task | 内容 | 状态 |
|------|------|------|
| Task 0 | MainViewModel MVVM 核心 | ✅ |
| Task 1 | SessionData 模型 + ChatMessage 增强 | ✅ |
| Task 2 | 侧边栏改造（会话区 + 折叠） | ✅ |
| Task 3 | ConversationView + CollectionViewSource + 上下文截断 | ✅ |
| Task 3.6-3.7 | BridgeProfile + instructor.apatch + ChatResponse/AnalysisResult Pydantic | ✅ |
| Task 3.8 | 删除 SpokenStreamParser (116 行) | ✅ |
| Task 3.9-3.10 | _dict_to_profile 强校验 + analyze_character instructor 化 | ✅ |
| Task 4 | ⑨模式主题联动 | ✅ |
| Task 5 | 内心独白全局开关 | ✅ |
| Task 6 | 属性面板折叠修复 | ✅ |
| Task 7 | LiteDB 持久化 | ✅ |
| Task 8 | 对话标题栏 | ✅ |

**产物**：dotnet 0 error, pytest 190/190, 图片嵌入 DLL, 启动 Loading 窗口

### desktop-polish — 安全性/可靠性打磨

| Task | 内容 | 状态 |
|------|------|------|
| Task 1 | 启动 Loading 窗口 | ✅ |
| Task 2 | 模态窗口 StaticResource → DynamicResource | ✅ |
| Task 3 | IO 线程隔离（File.ReadAllText → Task.Run） | ✅ |
| Task 4 | 4 处静默异常 → logging.warning | ✅ |
| Task 5 | config.py 字段去重 | ✅ |
| Task 6 | SliderItem → ObservableObject 迁移 | ✅ |
| Task 7 | MessageBox → NotificationService 统一 | ✅ |

### fix-binding-and-api — 数据绑定断裂修复

| Task | 内容 | 状态 |
|------|------|------|
| Task 1 | llm_caller.py 推理模型 Mode.JSON | ✅ |
| Task 2+4 | AttributePanel 10 硬编码 Slider 直接绑定 Profile | ✅ |
| Task 3 | ConversationView 标题栏显示角色名 | ✅ |
| Task 5 | API 配置持久化验证（无需改动） | ✅ |
| Task 6 | 删除会话 + ILocalStore.DeleteSession | ✅ |

### fix-role-save-and-ui — 角色创建保存 + UI 修复

| Task | 内容 | 状态 |
|------|------|------|
| Task 1 | 修复 base_url 残留 bug | ✅ |
| Task 2 | 属性面板移除人物背景 textarea | ✅ |
| Task 3 | 全界面"预设"→"角色" | ✅ |

### 安全审计 5 阶段 — 38/38 全部修复

| 阶段 | 修复项 | 状态 |
|------|--------|------|
| 阶段 1 | S01认证/S02脱敏/S03_diag/S04CORS/S05限流/S06输入/S07CSP/S09全量/S10模型/S16Settings | ✅ |
| 阶段 2 | S05限流/S08加密 | ✅ |
| 阶段 3 | S17双存储加密空洞/S18异常泄漏/S19Key落盘/S20流式透传/S21_error格式 | ✅ |
| 阶段 4 | F22 placeholder检查/F23 analyze_character日志/F24 SSE解析日志/F25 crypto精确化/F26 FERNET_KEY告警 | ✅ |
| 阶段 5 | D1-D11 上线前去匿名化（.pdb/.env/.db/.instance 清理 + 目录删除 + .gitignore 加固 + DeepSeek URL 修正） | ✅ |

**安全等级**：A（10🔴修复 + 12🟠修复 + 11🟡修复 + 3🟢修复 + 2🔵建议）

---

## 🔄 进行中

### fix-license-headers — 全项目 SPDX 版权头补全

| Task | 内容 | 状态 |
|------|------|------|
| Task 1 | Python 54 文件 SPDX 头注入 | ✅ 脚本就绪 |
| Task 2 | C# 26 文件 SPDX 头注入 | ✅ 脚本就绪 |
| Task 3 | .gitignore `*.spec` 修正 | ✅ 已修复 |
| 回归 | pytest 190/190 · dotnet 0 error | ⏳ |

**安全效果**：80 个源文件 100% 覆盖 SPDX-License-Identifier: AGPL-3.0-or-later，法律可执行

---

## ⏳ 规划中

### fix-residual-risks — 加密体系对齐 + SSRF 防护

| Task | 内容 | 状态 |
|------|------|------|
| Task 1 | 记忆摘要加密对齐（memory_entries 明文→密文） | ⏳ |
| Task 2 | Fernet 密钥持久化（`fernet.key` 文件 + crypto.py 惰性初始化） | ⏳ |
| Task 3 | SSRF 防护（base_url 校验禁止内网/localhost） | ⏳ |
| Task 4 | 辅助修复（日志参数化 + requirements.txt + C# 转义） | ⏳ |

**安全效果**：修复 4 项中危（R01 SSRF · R02 记忆加密 · R05 密钥持久化 · R09 依赖声明），安全等级 A- → A

### Phase 5+6 — 角色 Factory + TTS 语音

| Task | 内容 | 状态 |
|------|------|------|
| 待出 Spec | 知识域约束引擎 · 语音合成 | ⏳ |

---

## ❌ 废弃

### desktop-packaging — Tauri 桌面版

**废弃原因**：技术方案已从 Tauri（双进程 HTTP）变更为 WPF + pythonnet（单进程嵌入）。Tauri 分支不再维护，WPF 桌面版已完全替代其功能。

---

## 发布历史

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-07-01 | Beta v0.8 | 残余风险修复（记忆加密 · Fernet 持久化 · SSRF 防护 · 版权头规范） |
| 2026-06-28 | Beta v0.7 | 上线前去匿名化（.pdb/.db/.env/.toc 清理 + 构建产物加固 + .gitignore 完善 + 打包脚本 Stage 4 验证） |
| 2026-06-28 | Beta v0.6 | 三级 API fallback + 全量日志 + 崩溃防御 + 图片嵌入 DLL |
| 2026-06-27 | Beta v0.5 | MVVM 重构 + LiteDB + instructor + 10 硬编码 Slider + 会话删除 + ⑨主题联动 |
| 2026-06-26 | Alpha v0.4 | pythonnet 桥接 + 安全审计 4 阶段 27 修复 |
| 2026-06-25 | Alpha v0.3 | 角色创建保存 + UI 修复 + API 持久化 |

---

## 阻塞项

**无阻塞项。** 当前版本（Beta v0.8）开发中：

```
dotnet build: 0 error
pytest:       190 passed
安全审计:     A (38/38)
去匿名化:     11/11 PASS
完整度审计:   18/18 PASS
`fix-residual-risks` 为本迭代核心安全加固，完成后可达等级 A。
`fix-license-headers` 为 License 合规，非功能阻塞。
`Phase 5+6` 为非阻塞优化，可延后到 0.9 版本。
