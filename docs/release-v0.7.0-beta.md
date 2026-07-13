## MISS Beta v0.7

Beta 推进中 — 本次新增多人角色房间功能，DeepSeek 兼容修复，增量安全审计 13 项。

### 新增功能

| 功能 | 技术 | 文件 |
|------|------|------|
| **多人角色房间** | 后端广播模型 + C# pythonnet 桥接 + 房间感知 Prompt | `routers/room.py` (168行) + `room_bridge.py` (155行) + `PythonBridge.cs` (+64行) |

### 后端新增

| 文件 | 行数 | 功能 |
|------|------|------|
| `routers/room.py` | 168 | POST /api/room/chat + /api/room/chat/stream，Schema 校验 |
| `services/room_bridge.py` | 155 | 同步 wrapper for C# pythonnet bridge |
| `prompt_builder.py` | +63 | `build_room_prompt()` 房间感知上下文 |
| `models/session.py` | +2 | `room_type` + `room_roles` 字段 |
| `main.py` | +2 | 注册 room_router |

### C# 桌面端新增

| 文件 | 变更 | 功能 |
|------|------|------|
| `PythonBridge.cs` | +64行 | `RoomChat()` / `RoomChatStream()` + `RoomCharProfile` |
| `MainViewModel.cs` | +27行 | `RoomRoles` 集合 + `IsRoomMode` + Add/RemoveRoleToRoom |
| `RoleSidebar.xaml` | +3行 | 🏠 加入当前房间按钮 |
| `RoleSidebar.xaml.cs` | +13行 | 按钮逻辑 |

### Bug 修复

| 修复 | 内容 |
|------|------|
| **DeepSeek 流式沉默失败** | 5 项修复：config `deepseek_skip_instructor`、chat router 流式检测、llm_caller raw 调用路径、memory_manager/prompt_builder 兼容 |
| **DeepSeek 非流式 instructor** | `_call_raw` 方法，非流式请求也跳过 instructor 包装 |
| **Publish 安全清理** | 移除 PDB 调试符号 + DB 残留（miss.db / miss.db-shm / miss.db-wal） |

### 安全增量审计（N01-N13）

| Phase | 项目 | 说明 |
|-------|------|------|
| **A（发布阻塞）** | N01+N02 | publish 清理 .pdb / .db |
| **B（本周）** | N03-N06, N10-N13 | build.ps1 验证、localStorage→sessionStorage（10处）、except→logger、max_length=8、Schema 校验、无裸 pass、测试更新 |

**累计安全修复**: 51/51（原 38 + 增量 13），安全等级 A

### UI 新增

- 🏠 RoleSidebar「加入当前房间」按钮
- 房间模式：多角色同时对话，角色间互动
- 单人模式不受影响

### Spec 交付

| Spec | 内容 | 状态 |
|------|------|:---:|
| `multi-character-room` | 多人角色房间 — 后端 + C# 桥接 + UI | ✅ PASS |
| DeepSeek 兼容修复 | 流式 + 非流式 2 轮修复 | ✅ PASS |
| 安全增量审计 | N01-N13 修复 | ✅ PASS |

### 累计统计（Beta v0.7）

```
提交：54 次
pytest：~190/190
xUnit：9/9 PASS
安全：A（51/51）
Spec：15/15 PASS
想法池：3 项
标准文件：8/8
Git Tag：v0.7.0-beta
```

Contributing: read [CLA.md](https://github.com/luyi14-bits/MISS-project/blob/master/CLA.md) — PR submission is acceptance.
