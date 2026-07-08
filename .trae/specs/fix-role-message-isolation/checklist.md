# Checklist

## Bug A: 角色切换消息隔离
- [x] `OnCurrentRoleChanged` 中有 `LocalStore.SaveMessages` 保存当前消息
- [x] `OnCurrentRoleChanged` 中有 `_allMessages.Clear()` 清空
- [x] `OnCurrentRoleChanged` 中有按 `RoleName` 过滤的 `LocalStore.LoadMessages` 重新加载
- [x] `Filter` 的 `IsUser` 规则不变（L62-L68 无需修改）
- [ ] 与小恶魔聊 3 条 → 切到小天使 → 对话栏清空（或显示小天使历史）
- [ ] 切回小恶魔 → 对话栏恢复之前的 3 条消息（双方都有）

## Bug B: session_id 角色隔离
- [ ] `SendMessage()` 中 sessionId 格式为 `sess_{Id}_{roleName}`
- [ ] `SendMessageStream()` 中 sessionId 格式为 `sess_{Id}_{roleName}`
- [ ] Python 侧无改动
- [ ] 与小恶魔聊天 + 切到小天使聊天 → Python `get_window()` 返回的消息列表只含当前角色

## 回归
- [ ] 正常对话：新建会话 → 选角色 → 发消息 → 回复正常
- [ ] 切换会话：切到其他 session → `OnCurrentSessionChanged` 原逻辑正常
- [ ] 角色分析：新建角色 → 分析 → 切换 → 消息隔离正确
- [ ] 流式对话：切换角色后流式消息 token 正常推送
- [x] dotnet build 0 error
- [x] pytest 183/183 无回归
