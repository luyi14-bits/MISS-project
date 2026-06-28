# Tasks

- [ ] Task 1: 修复 `_get_client()` 的 base_url 残留 bug
  - [ ] SubTask 1.1: 修改 `routers/character.py` 第 19-23 行，`if base:` 改为始终更新 `_client.base_url`，并每次重建 `AsyncOpenAI` 实例而非复用
- [ ] Task 2: 从属性面板移除"人物背景" textarea
  - [ ] SubTask 2.1: 删除 `index.html` 中侧边栏属性面板内的 `characterBackground` 相关 HTML（约 L375-L382）
  - [ ] SubTask 2.2: 删除 `saveCurrentPreset` 中对 `characterBackground` 的读取，改为固定的空字符串
  - [ ] SubTask 2.3: 删除 `sendMsg` 中对 `characterBackground` 的读取，改为从预设数据获取或为空
  - [ ] SubTask 2.4: 删除 `loadAndApplyPreset` 中对 `characterBackground` 的写回
  - [ ] SubTask 2.5: 删除 `createPresetFromModal` 中对 `characterBackground` 的写回
  - [ ] SubTask 2.6: 新建弹窗创建成功后，将弹窗中的背景值写入 `appliedProfile` 或传递给 `sendMsg`
- [ ] Task 3: 全界面"预设"改为"角色"
  - [ ] SubTask 3.1: 侧边栏标题、按钮 tooltip、收起态文字中的"预设"→"角色"
  - [ ] SubTask 3.2: 空状态 HTML 模板字符串中的"预设"→"角色"
  - [ ] SubTask 3.3: 右键菜单和 toast 文案中的"预设"→"角色"
  - [ ] SubTask 3.4: JS 函数注释、变量默认值 (`'新预设'` → `'新角色'`)、prompt 文案中的"预设"→"角色"
  - [ ] SubTask 3.5: CSS 注释"预设卡片"→"角色卡片"

# Task Dependencies
- Task 2 不依赖 Task 1
- Task 3 不依赖 Task 1 或 Task 2
- 三个 Task 可以并行执行
