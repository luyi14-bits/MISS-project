# Tasks

- [ ] Task 1: Bug A — 角色切换消息隔离（MainViewModel.cs）
  - [ ] SubTask 1.1: 修改 `OnCurrentRoleChanged` L77-L88：
    - ① 调 `LocalStore.SaveMessages(_currentSession.Id, _allMessages.ToList())` 保存当前消息
    - ② `_allMessages.Clear()` 清空
    - ③ 调 `LocalStore.LoadMessages(_currentSession.Id)` → 过滤器：`m.IsUser || m.RoleName == value?.Name` → 加载到 `_allMessages`
    - ④ `_currentSession.RoleName = value?.Name`
  - [ ] SubTask 1.2: 保留 `Filter` 的 `IsUser` 规则不变（不需要改 L62-L68）
  - [ ] SubTask 1.3: 确保首次创建角色时 `value` 不为 null → 消息正常加载（空列表）

- [ ] Task 2: Bug B — session_id 加角色名（MainViewModel.cs）
  - [ ] SubTask 2.1: 搜索 `_currentSession.Id` 构造 sessionId 的位置（`SendMessage` + `SendMessageStream`）
  - [ ] SubTask 2.2: 将 `sess_{_currentSession.Id}` 改为 `sess_{_currentSession.Id}_{_currentRole?.Name ?? "default"}`
  - [ ] SubTask 2.3: Python 侧零改动。验证 `memory_manager.get_window()` 不再返回跨角色混合消息

# Task Dependencies
- Task 1 和 Task 2 可并行（改不同位置）

# 技术要点
- **不改 Filter**：`IsUser` 规则不变——消息隔离由加载过滤保证，Filter 只在已加载集合内生效
- **不改 Python**：`session_id` 从 `sess_1` 改为 `sess_1_小恶魔` 后，SQLite 自动物理隔离
- **不新增数据结构**：复用现有 `LocalStore.SaveMessages/LoadMessages`（SubTask 1.1 的步骤①③）
- **LiteDB 读写**：每次角色切换有两次本地 DB 操作（保存+加载），微秒级延迟，用户无感知
