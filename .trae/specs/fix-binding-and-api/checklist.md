# Checklist

## Task 1: 推理模型兼容性
- [ ] `llm_caller.py` 中 `_REASONING_MODELS = {"reasoner", "o1", "o3"}` 常量存在
- [ ] `_ensure_client()` 对推理模型使用 `instructor.Mode.JSON`（非 `TOOLS`）
- [ ] 用户选择 `deepseek-reasoner` + 发送消息 → 无 400 报错 → 正常解析 JSON

## Task 2: 属性面板跟随角色切换
- [ ] `MainViewModel.cs` 新增 10 个 `[ObservableProperty]`（10 维属性）
- [ ] `OnCurrentRoleChanged` 中将 `CurrentRole.Profile.XXX` 赋值给 10 个属性
- [ ] `OnCurrentRoleChanged` 中设 `IsCirnoMode = (EducationLevel == -100)`
- [ ] `OnIsCirnoModeChanged` 中调用 `App.SetTheme(IsCirnoMode)`
- [ ] 点击"傲娇女友"→ 属性面板 Slider 更新为非零值
- [ ] 点击"笨蛋⑨"→ ⑨模式激活（冰蓝色调）

## Task 3: 对话视图角色感知
- [ ] `ConversationView.xaml` 标题栏显示 `CurrentRole.Name`
- [ ] `CurrentRole` 为空时显示"未指定角色"
- [ ] 切换角色后标题栏文字实时更新

## Task 4: 属性面板 XAML 绑定
- [ ] Slider `Value` 绑定到 `MainViewModel.XXX`（非本地 `SliderItem.Value`）
- [ ] 文化水平 Slider 拖至 -100 → `IsCirnoMode = true`
- [ ] 文化水平 Slider 拖离 -100 → `IsCirnoMode = false`

## Task 5: API 配置持久化
- [ ] `PythonBridge.ApplySettings()` 调 `LocalStore.SaveSettings()` 落盘
- [ ] 启动时 `LocalStore.LoadSettings()` 恢复 + 调用 `PythonBridge.ApplySettings()` 同步
- [ ] 重启 MISS.exe → API Key / Base URL / 模型 不丢失

## Task 6: 删除会话
- [ ] `RoleSidebar.xaml` 会话列表中每个项有 ✕ 删除按钮
- [ ] `MainViewModel.DeleteSessionCommand` 存在（`[RelayCommand]`）
- [ ] 删除会话 → `_sessions` 移除 + LiteDB 物理删除
- [ ] 删除当前会话 → 自动切换到下一个会话

## 验收
- [ ] dotnet build 0 error
- [ ] pytest 183/183 无回归
- [ ] 选择笨蛋⑨→ 冰蓝主题生效
- [ ] 选择傲娇女友 → 属性面板滑块非零
- [ ] 设置 API Key → 重启 → 配置仍在
