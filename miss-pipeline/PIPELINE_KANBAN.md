# MISS 项目管线看板

> 更新时间：2026-06-28 · 当前发布版本：Beta v0.7

---

## 状态总览

| 状态 | Spec 数 | 说明 |
|------|---------|------|
| ✅ **已完成** | 5 | 已发布/验收通过 |
| 🔄 **进行中** | 1 | 部分完成，核心功能已上线 |
| ⏳ **待开工** | 1 | 未启动 |
| ❌ **废弃** | 1 | 技术方案变更（Tauri → pythonnet） |

---

## ✅ 已完成

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

### fix-llm-api-compat — API 兼容性 + 三级 fallback

| Task | 内容 | 状态 |
|------|------|------|
| Task 1 | `call()` 三级 fallback（TOOLS → JSON → 裸API） | ✅ 已实现 |
| Task 1.1-1.3 | 三级拆方法（简化为 try/except 链） | ✅ 已实现 |
| Task 1.4 | `_call_level3()` json.loads 失败 → 安全占位符（非原文） | ✅ 已实现 |
| Task 1.5 | 每次调用完成写入 INFO 日志 | ✅ 已实现 |
| Task 1.6 | `analyze_character()` 三级 fallback + 日志 | ✅ 已实现 |
| Task 1 extra | 5 处静默异常加 logging.warning | ✅ 已实现 |
| Task 2 | `_is_reasoning_model()` 检测 | ✅ 已实现 |
| Task 3 | `POST /api/settings/test` 端点增强 | ⏳ 待开工 |
| Task 4 | pytest 回归验证 | ⏳ 待开工 |

**说明**：核心功能（三级 fallback + 推理模型检测 + 全量日志）已实装上线。Task 3（测试端点增强）属于可观测性优化，非阻塞发布。

---

## ⏳ 待开工

### fix-role-message-isolation — 角色切换消息隔离

| Task | 内容 | 状态 |
|------|------|------|
| Task 1 | 角色切换时消息隔离（save→clear→load filtered） | ⏳ |
| Task 2 | session_id 加角色名 | ⏳ |

**预期工作量**：~20 行 C#（MainViewModel.cs），0 行 Python

---

## ❌ 废弃

### desktop-packaging — Tauri 桌面版

**废弃原因**：技术方案已从 Tauri（双进程 HTTP）变更为 WPF + pythonnet（单进程嵌入）。Tauri 分支不再维护，WPF 桌面版已完全替代其功能。

---

## 发布历史

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-06-28 | Beta v0.7 | 上线前去匿名化（.pdb/.db/.env/.toc 清理 + 构建产物加固 + .gitignore 完善 + 打包脚本 Stage 4 验证） |
| 2026-06-28 | Beta v0.6 | 三级 API fallback + 全量日志 + 崩溃防御 + 图片嵌入 DLL |
| 2026-06-27 | Beta v0.5 | MVVM 重构 + LiteDB + instructor + 10 硬编码 Slider + 会话删除 + ⑨主题联动 |
| 2026-06-26 | Alpha v0.4 | pythonnet 桥接 + 安全审计 4 阶段 27 修复 |
| 2026-06-25 | Alpha v0.3 | 角色创建保存 + UI 修复 + API 持久化 |

---

## 阻塞项

**无阻塞项。** 当前版本（Beta v0.7）可直接发布：

```
dotnet build: 0 error
pytest:       190 passed
安全审计:     A (38/38)
去匿名化:     11/11 PASS
完整度审计:   18/18 PASS
```

`fix-role-message-isolation` 为非阻塞优化，可延后到 0.8 版本。
