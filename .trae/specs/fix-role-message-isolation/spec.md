# fix-role-message-isolation Spec — 角色切换消息隔离

## Why
修复组诊断报告确认两个独立 Bug，均导致角色切换后消息混乱：

1. **Bug A（🔴 前端）**：`_messagesViewSource.Filter` 的 `if (m.IsUser) return true` 让所有用户消息永远可见。角色切换时仅 `Refresh()` 重新跑 Filter，不从 `_allMessages` 中清除旧角色消息 → 用户看到小天使和小恶魔的混合历史
2. **Bug B（🟠 后端）**：Python `session_id = sess_{Id}` 不含角色名。`memory_manager.get_window()` 按 session 查全部消息，不按角色过滤 → LLM 收到两个角色的混合上下文 → 角色串线

根因：`SessionData.RoleName` 是 session 级单值绑定（一对一），但实际使用中一个 session 可以有多个角色（一对多），代码没有"角色上下文"隔离消息。

## What Changes
- **MainViewModel.cs** `OnCurrentRoleChanged`：增加保存→清空→按角色重新加载三步逻辑（复用现有 `LocalStore.SaveMessages/LoadMessages`）
- **MainViewModel.cs** `SendMessage()` / `SendMessageStream()`：`sessionId` 从 `sess_{Id}` 改为 `sess_{Id}_{roleName}`
- Python 侧 **零改动**：`memory_manager.py`、`prompt_builder.py` 代码不变，物理隔离自动生效

## Impact
- Affected code: `ViewModels/MainViewModel.cs`（OnCurrentRoleChanged + sessionId 构造）
- 不改: `memory_manager.py`, `prompt_builder.py`, `CollectionViewSource Filter`

---

## ADDED Requirements

### Requirement: Bug A — 角色切换时消息隔离
The system SHALL 在 `OnCurrentRoleChanged` 中以"保存当前 → 清空 → 按角色加载"三步实现消息隔离。

```csharp
partial void OnCurrentRoleChanged(RoleData? value)
{
    if (value != null)
        IsCirnoMode = value.Profile.EducationLevel == -100;

    DispatcherHelper.Run(() =>
    {
        if (_currentSession != null)
        {
            // ① 保存当前消息到 LiteDB（防切换丢失）
            LocalStore.SaveMessages(_currentSession.Id, _allMessages.ToList());

            // ② 清空
            _allMessages.Clear();

            // ③ 按角色重新加载：用户消息（IsUser）OR RoleName 匹配 → 加载
            var msgs = LocalStore.LoadMessages(_currentSession.Id);
            foreach (var m in msgs)
            {
                if (m.IsUser || m.RoleName == value?.Name)
                    _allMessages.Add(m);
            }

            _currentSession.RoleName = value?.Name;
        }

        _messagesViewSource.View.Refresh();
    });
}
```

**保留** `Filter` 的 `IsUser` 规则不变——因为在步骤③中已经通过加载过滤保证了消息隔离，Filter 的 IsUser 条件变成了"在当前已加载的消息集合中永远显示用户消息"（正确行为）。

#### Scenario: 切换角色
- **WHEN** 用户与小恶魔聊 3 条 → 点击小天使
- **THEN** 对话栏清空 → 只显示小天使的历史消息（若有）或空白（新角色）

#### Scenario: 切回旧角色
- **WHEN** 用户切回小恶魔
- **THEN** 对话栏恢复之前与小恶魔的 3 条消息（双方都有）

### Requirement: Bug B — Python 后端 session_id 角色隔离
The system SHALL 将 C# 侧的 `sessionId` 从 `sess_{Id}` 改为 `sess_{Id}_{roleName}` 格式。

```csharp
// SendMessage() / SendMessageStream() — 改动一行
string sessionId = $"sess_{_currentSession.Id}_{_currentRole?.Name ?? "default"}";
```

Python 侧 **零改动**：`memory_manager.get_window(session_id)` 的 session_id 参数仍是 string，`sess_1_小恶魔` 和 `sess_1_小天使` 在 SQLite 中物理隔离——不同 session_id = 不同行。

#### 技术选型：为什么物理隔离而不是加参数过滤

| 方案 | 优点 | 缺点 |
|------|------|------|
| 物理隔离（选中）| 零 Python 改动；零性能开销；零 bug 面 | session_id 包含角色名（非纯 UUID） |
| get_window 加 role_name 参数 | session_id 保持语义纯净 | 需要改 3 个 Python 文件；新增过滤逻辑引入新 bug 面 |

选择物理隔离——不同角色的消息本来就不应该在同一个 SQLite 分区里混存。

#### Scenario: 不同角色上下文隔离
- **WHEN** 用户与小恶魔聊完后切到小天使 → 发送"你好"
- **THEN** LLM 收到的上下文只包含小天使的历史消息（不包含小恶魔的对话）
