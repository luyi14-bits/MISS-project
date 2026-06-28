# Checklist

- [ ] `routers/character.py` 中 `_get_client()` 每次调用都重建 `AsyncOpenAI` 实例，不复用旧实例
- [ ] `routers/character.py` 中 `_get_client()` 不再依赖 `if base:` 条件更新 base_url
- [ ] `index.html` 属性面板中不包含 `id="characterBackground"` 的 textarea
- [ ] `saveCurrentPreset` 中不再读取 `document.getElementById('characterBackground')`
- [ ] `sendMsg` 中不再读取 `document.getElementById('characterBackground')`，背景从 `appliedProfile` 或预设数据获取
- [ ] `loadAndApplyPreset` 中不再对 `characterBackground` 做写回操作
- [ ] `createPresetFromModal` 中不再对 `characterBackground` 做写回操作
- [ ] 新建弹窗创建成功后背景值正确传递到后续聊天请求
- [ ] 侧边栏标题显示"角色"而非"预设"
- [ ] 新建/保存/导入按钮 tooltip 显示"角色"而非"预设"
- [ ] 空状态引导文字显示"角色"而非"预设"
- [ ] toast 提示文案显示"角色"而非"预设"
- [ ] JS 中变量默认值和 prompt 弹出文字显示"角色"而非"预设"
- [ ] 连续两次通过弹窗创建角色均成功，无 LLM 异常
