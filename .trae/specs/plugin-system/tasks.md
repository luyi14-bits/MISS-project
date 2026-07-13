# 插件系统 — 任务拆分

> 总估时：5d · 优先级：P1 · 依赖：Python FastAPI 后端 + C# WPF 前端

---

- [ ] Task 1: Python 插件引擎（核心）
  - [ ] SubTask 1.1: `services/plugin_manager.py` — 插件发现 + 加载 + 生命周期管理
  - [ ] SubTask 1.2: 钩子系统 — `on_message` / `on_role_change` / `on_app_start` / `on_app_exit`
  - [ ] SubTask 1.3: `plugin.json` 清单解析 + 校验
  - [ ] SubTask 1.4: JSON-RPC 子进程通信协议定义（stdin/stdout）
  - [ ] SubTask 1.5: 沙箱隔离 — subprocess + 超时 + 内存限制 + 写权限控制
  - 验收：`python -m pytest tests/test_plugin_manager.py` 通过
  - 估时：2d

- [ ] Task 2: C# PluginBridge
  - [ ] SubTask 2.1: `Services/PluginBridge.cs` — `GetPlugins()` / `GetPluginInfo(name)` / `InvokePluginHook(name, hook, payload)`
  - [ ] SubTask 2.2: Python 后端 API `/api/plugins/*` 代理调用
  - [ ] SubTask 2.3: 插件事件回调（C# 侧监听插件生命周期）
  - 验收：`dotnet test` 通过
  - 估时：1.5d

- [ ] Task 3: UI 插件面板
  - [ ] SubTask 3.1: ConversationView 或 Settings 新增"插件"选项卡
  - [ ] SubTask 3.2: 已安装插件列表（名称/版本/作者/开关）
  - [ ] SubTask 3.3: 插件状态指示灯（运行中/已停止/错误）
  - 验收：publish 产物中插件面板可见
  - 估时：1d

- [ ] Task 4: 示例插件 + 文档
  - [ ] SubTask 4.1: 写一个示例插件（"消息统计"：统计每日对话字数）
  - [ ] SubTask 4.2: `docs/plugin-dev-guide.md` — 插件开发指南
  - 验收：示例插件能正常加载并输出统计
  - 估时：0.5d
