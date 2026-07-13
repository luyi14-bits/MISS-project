# Spec: multi-character-room — 多人角色房间

## Why

当前 MISS 的对话模型是 **1:1（用户 ↔ 单角色）** 。用户只能与一个角色轮流对话。多人角色房间让用户在一个会话中同时与**多个 AI 角色**互动，角色之间也能感知彼此的存在和发言。这是从"和一个人聊"到"一个房间的人都在聊"的体验跃迁。

## Meta

| 属性 | 值 |
|------|-----|
| **优先级** | P1（体验核心） |
| **估时** | 4d |
| **依赖** | 无（独立功能，不修改现有 chat 管道） |

## What Changes

### New files
- `miss-backend/routers/room.py` — Room chat REST API
- `miss-backend/services/room_bridge.py` — Room-aware Python→C# bridge
- `.trae/specs/multi-character-room/` — Spec 文件

### Modified files
- `miss-backend/models/session.py` — 新增 `room_type` 字段
- `miss-backend/models/message.py` — `role` 字段扩展为支持 `"character:Alice"` 格式
- `miss-backend/services/prompt_builder.py` — 新增房间感知 prompt 构造
- `miss-desktop-wpf/Services/PythonBridge.cs` — 新增 `RoomChat()` / `RoomChatStream()`
- `miss-desktop-wpf/ViewModels/MainViewModel.cs` — 新增 `_roomRoles` 集合 + 角色管理
- `miss-desktop-wpf/Views/ConversationView.xaml` — 多角色气泡渲染
- `miss-desktop-wpf/Views/RoleSidebar.xaml/.cs` — "加入房间"功能

## Impact

| 域 | 影响 | 说明 |
|------|:----:|------|
| 数据库 | 🟡 中 | Session 表新增字段，现有数据兼容 |
| API | 🟡 中 | 新增端点，不影响现有 /api/chat |
| UI | 🟡 中 | ConversationView 新增房间角色栏 |
| 安全 | 🟡 中 | 角色间上下文传递需防提示词注入 |

## ADDED Requirements

1. 系统提示词必须包含房间内所有角色的名称和人格摘要
2. 每个角色的 LLM 调用必须并行发出（`asyncio.gather()`）
3. 角色 B 的回复应能感知角色 A 刚说的内容
4. 对话栏显示房间内全部消息，不按单角色过滤
5. 用户可以动态添加/移除房间中的角色
6. 单人角色房间退化为普通对话（兼容现有功能）
