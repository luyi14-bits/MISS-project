# Tasks

- [ ] Task 1: 推理模型兼容性修复（llm_caller.py）
  - [ ] SubTask 1.1: 定义 `_REASONING_MODELS = {"reasoner", "o1", "o3"}` 常量 + `_is_reasoning_model(model)` 函数
  - [ ] SubTask 1.2: `_ensure_client()` L48：将 `instructor.apatch(client, mode=instructor.Mode.TOOLS)` 改为根据 `_is_reasoning_model(current_model)` 动态选择 `Mode.JSON` 或 `Mode.TOOLS`

- [ ] Task 2: 属性面板跟随角色切换（MainViewModel.cs）
  - [ ] SubTask 2.1: 新增 10 个 `[ObservableProperty]`：`_educationLevel`, `_rationalEmotional`, `_willpower`, `_independentSubmissive`, `_intimacy`, `_curiosity`, `_humor`, `_aggression`, `_socialEnergy`, `_adventurousness`
  - [ ] SubTask 2.2: `OnCurrentRoleChanged` 中：若 `value != null`，将 `value.Profile` 的 10 个属性值赋给上述 10 个 `[ObservableProperty]`；同时设 `IsCirnoMode = value.Profile.EducationLevel == -100`
  - [ ] SubTask 2.3: `OnIsCirnoModeChanged` 中：调用 `App.SetTheme(IsCirnoMode)`

- [ ] Task 3: 对话视图角色感知（ConversationView.xaml）
  - [ ] SubTask 3.1: 在标题栏 `CurrentSession.Title` 旁新增 `TextBlock` 绑定 `CurrentRole.Name`（`TargetNullValue='未指定角色'`）

- [ ] Task 4: 属性面板 XAML 绑定（AttributePanel.xaml + ConversationView.xaml）
  - [ ] SubTask 4.1: `AttributePanel.xaml` 中 Slider `Value` 绑定改为 `{Binding EducationLevel, Mode=TwoWay}`（非本地 `SliderItem.Value`）
  - [ ] SubTask 4.2: `CultureLevel` Slider `ValueChanged` 事件中：`education_level == -100` → `VM.IsCirnoMode = true`

- [ ] Task 5: API 配置持久化（PythonBridge.cs + App.xaml.cs）
  - [ ] SubTask 5.1: `PythonBridge.ApplySettings()` 增强 → 先调 `desktop_bridge.apply_settings()` 同步内存 → 再调 `LocalStore.SaveSettings()` 落盘
  - [ ] SubTask 5.2: `App.xaml.cs` `OnStartup` 中：`LocalStore.LoadSettings()` 恢复 → `PythonBridge.ApplySettings()` 同步 Python 侧运行时

- [ ] Task 6: 删除会话功能（RoleSidebar.xaml + MainViewModel.cs）
  - [ ] SubTask 6.1: `RoleSidebar.xaml` 会话 ListBox `ItemTemplate` 新增删除按钮（✕）→ `Command="{Binding DataContext.DeleteSessionCommand, ...}"`
  - [ ] SubTask 6.2: `MainViewModel.cs` 新增 `[RelayCommand] DeleteSession(SessionData)` → 从 `_sessions` 移除 + `LocalStore.DeleteSession(id)` + 若为目标会话则切换到下一个

# Task Dependencies
- Task 1 可并行（仅 Python 侧）
- Task 2 依赖 Task 4（需先有 10 个属性绑定目标）
- Task 3 无依赖
- Task 4 可并行于 Task 2
- Task 5 无依赖
- Task 6 无依赖

# 技术要点
- **推理模型检测**：简单 `"reasoner" in model.lower()` 字符串匹配，不做复杂正则
- **10 个属性绑定**：从 `SliderItem.Value` 改为直接绑定 `MainViewModel.XXX` 属性（`{Binding EducationLevel, RelativeSource={RelativeSource AncestorType=Window}}`）
- **⑨模式触发路径**：`OnCurrentRoleChanged` → `IsCirnoMode = true/false` → `OnIsCirnoModeChanged` → `App.SetTheme()`
