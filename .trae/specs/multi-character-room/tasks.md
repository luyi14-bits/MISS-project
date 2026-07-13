# Tasks: multi-character-room

## Task 1: 后端 room 端点（~2d）

**目标**：创建独立的 room chat API，支持多角色并行 LLM 调用。

**输入**：`room_id`, `message`, `character_ids`
**输出**：`List[ChatResponse]` （每个角色一个回复）

| SubTask | 内容 | 依赖 |
|---------|------|------|
| 1.1 | `models/session.py` 新增 `room_type` 字段（`"single"` / `"room"`），默认 `"single"` | 无 |
| 1.2 | `models/message.py` 扩展 `role` 字段支持 `"character:Alice"` 格式 | 1.1 |
| 1.3 | `routers/room.py` — `POST /api/room/chat` + `POST /api/room/chat/stream` | 无 |
| 1.4 | `services/prompt_builder.py` — 新增 `build_room_prompt()`，注入所有角色信息 | 1.1 |
| 1.5 | `asyncio.gather()` 并行 N 个 LLM 调用 | 1.3+1.4 |
| 1.6 | `services/room_bridge.py` — `room_chat()` / `room_chat_stream()` 同步包装 | 1.3 |

**验收标准**：
- 发一条消息到房间 → 返回 N 个角色的回复
- 每个回复包含 `inner_thought` + `spoken` + `intimacy_change`
- N=1 时行为与普通 chat 一致
- `pytest` 新增 `test_room.py`，至少 5 个测试

---

## Task 2: C# 桥接 + ViewModel（~1.5d）

**目标**：Python bridge 新增 room 方法，MainViewModel 管理多角色集合。

| SubTask | 内容 | 依赖 |
|---------|------|------|
| 2.1 | `PythonBridge.cs` 新增 `RoomChat()` / `RoomChatStream()` | Task 1.6 |
| 2.2 | `MainViewModel.cs` 新增 `_roomRoles: ObservableCollection<RoleData>` | 无 |
| 2.3 | `AddRoleToRoom(RoleData)` / `RemoveRoleFromRoom(RoleData)` 方法 | 2.2 |
| 2.4 | `MessagesView` Filter 改为：房间模式显示全部消息；单人模式按角色过滤 | 2.2+2.3 |
| 2.5 | 并行流式重写 `SendMessageStream`：为每个角色创建独立 `ChatMessage` + 独立 `ChatStream` | 2.1 |

**验收标准**：
- 添加 2 个角色到房间 → 发消息 → 收到 2 个角色的回复气泡
- 移除角色 → 该角色不再出现
- 单人房间（1 个角色）→ 行为与旧版一致

---

## Task 3: WPF UI 调整（~0.5d）

**目标**：ConversationView 渲染多角色气泡 + 房间角色栏。

| SubTask | 内容 | 依赖 |
|---------|------|------|
| 3.1 | `ConversationView.xaml` 验证 `ItemsControl` 已正确显示 `Sender` 名字 | Task 2.2 |
| 3.2 | 在输入栏上方新增"当前房间角色"行，显示头像+名字的小标签 | Task 2.2 |
| 3.3 | `RoleSidebar.xaml` — 右键菜单新增"加入当前房间" | Task 2.3 |

**验收标准**：
- 角色头顶显示各自的名字
- 房间角色栏可视、可管理
- 右键"加入房间"功能可用

---

## Task 4: 端到端验收（~0.5d）

**目标**：全链路验证 + 测试覆盖。

| SubTask | 内容 | 依赖 |
|---------|------|------|
| 4.1 | pytest `test_room.py` — 广播/边界/角色响应感知/1人退化为普通/压力 | Task 1 |
| 4.2 | xUnit `MainViewModel` 测试 — 角色集合管理/Filter 切换 | Task 2 |
| 4.3 | `dotnet publish` 验收 — 双击 MISS.exe 测试 | Task 3 |
| 4.4 | 更新管线看板 | — |

**验收标准**：
- pytest 新增 ≥5 个测试全部 PASS
- xUnit 新增 ≥3 个测试全部 PASS
- dotnet publish 0 error
- 手动测试：3 角色房间 → 发消息 → 3 个回复均出现
