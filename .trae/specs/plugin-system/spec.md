# 插件系统 (Plugin System)

> **Why**: 当前 MISS 的功能都是硬编码在代码中的。插件系统允许第三方开发者通过标准接口扩展 MISS 功能，无需修改核心代码。这是打开生态的第一步。
>
> **Meta**: 优先级 P1 · 估时 5d · 风险 🟡 中（进程隔离复杂性）

---

## What Changes

1. **Python 端** — 新增 `services/plugin_manager.py`：插件发现 + 加载 + 钩子系统 + 进程隔离
2. **C# 端** — 新增 `Services/PluginBridge.cs`：C# 侧访问插件服务的接口
3. **UI** — ConversationView 新增插件面板/菜单入口
4. **文档** — 插件开发指南 `docs/plugin-dev-guide.md`

## Impact

- Core modules: **不变** — 插件系统通过钩子(Hook)与核心通信，不侵入现有业务代码
- Performance: 无显著影响（插件在需要时才加载）
- Security: **需 STRIDE 建模** — 第三方代码必须沙箱隔离

---

## Requirements

### ADDED

1. 插件目录约定：`%APPDATA%/MISS/plugins/<plugin_name>/`，含 `plugin.json` 清单文件
2. 插件清单 (`plugin.json`)：name / version / author / description / hooks / permissions
3. 钩子系统 (`Hook`)：`on_message` / `on_role_change` / `on_app_start` / `on_app_exit`
4. 插件作为独立 Python 子进程运行，主进程通过 stdin/stdout JSON-RPC 通信
5. 子进程资源限制：5s 超时 / 64MB 内存上限 / 禁止文件系统写操作（除非声明 `permissions: ["write"]`）
6. C# `PluginBridge` 接口：`GetPlugins()` / `GetPluginInfo(name)` / `InvokePluginHook(name, hook, payload)`
7. UI 插件面板：列出已安装插件 + 开关 + 状态指示

### MODIFIED

- 无。插件系统是纯新增架构，不影响现有代码。

### REMOVED

- 无。
