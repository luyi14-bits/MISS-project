# Checklist: multi-character-room

## Backend

- [ ] Session 模型新增 `room_type` 字段（`"single"` / `"room"`）
- [ ] Message 模型 `role` 支持 `"character:Alice"` 格式
- [ ] `POST /api/room/chat` 接受多角色请求并返回多回复
- [ ] `POST /api/room/chat/stream` SSE 流式多角色推送
- [ ] `PromptBuilder.build_room_prompt()` 注入房间所有角色信息
- [ ] `asyncio.gather()` 并行 N 个 LLM 调用
- [ ] pytest `test_room.py` ≥5 个测试全部 PASS

## C# Bridge + ViewModel

- [ ] `PythonBridge.RoomChat()` / `RoomChatStream()` 可调用
- [ ] `MainViewModel` 新增 `_roomRoles` 集合
- [ ] `AddRoleToRoom()` / `RemoveRoleFromRoom()` 功能正常
- [ ] 房间模式 → MessagesView 显示全部消息
- [ ] 单人模式 → MessagesView 按角色过滤（兼容旧版）
- [ ] 并行流式：N 角色 → N 个消息气泡同时更新
- [ ] xUnit ≥3 个测试全部 PASS

## UI

- [ ] 角色气泡显示各自名字
- [ ] 输入栏上方有"当前房间角色"栏
- [ ] RoleSidebar 右键"加入当前房间"可用
- [ ] 移除角色后该角色不再出现

## E2E

- [ ] dotnet build 0 error
- [ ] dotnet publish 0 error
- [ ] 手动测试：3 角色房间 → 发消息 → N 个回复
- [ ] 手动测试：单人房间 → 行为与旧版一致
