# fix-binding-and-api Spec — 数据绑定断裂 + API 兼容性修复

## Why
用户验收发现 6 个核心缺陷：
1. 推理模型（deepseek-reasoner, o1-mini）触发 `Thinking mode does not support tool_choice` 400 崩溃——`instructor.Mode.TOOLS` 不兼容思考模式模型
2. 右侧属性面板点击不同角色时滑块全是 0，不跟随切换更新
3. 对话视图无当前角色感知——切换角色后不知道在和谁聊天
4. ⑨模式（文化水平=-100）不生效——`SetTheme` 方法存在但 `OnCurrentRoleChanged` 中未调用
5. API 配置无法持久化——重启后 API Key / Base URL 变空白（仅写内存 `_runtime_overrides`，未落盘）
6. 侧边栏无删除会话入口

## What Changes
- **llm_caller.py**：`_ensure_client()` 增加推理模型检测，对 `reasoner`/`o1`/`o3` 模型使用 `instructor.Mode.JSON` 替代 `TOOLS`
- **MainViewModel.cs**：`OnCurrentRoleChanged` 增加⑨模式触发（`IsCirnoMode = role.EducationLevel == -100`） + 属性面板自动加载 `CurrentRole.Profile`
- **ConversationView.xaml**：标题栏增加当前角色名/头像绑定
- **App.xaml.cs**：`OnStartup` 中将 `SetTheme` 改为 `IsCirnoMode` 属性变更时触发
- **PythonBridge.cs / desktop_bridge.py**：`apply_settings` 增加落盘写入（LiteDB + `.env` 文件）
- **RoleSidebar.xaml**：会话列表 ItemTemplate 增加删除按钮 → 绑定 `DeleteSessionCommand`

## Impact
- Affected specs: desktop-rebuild, desktop-polish
- Affected code: `llm_caller.py`, `MainViewModel.cs`, `ConversationView.xaml(.cs)`, `App.xaml.cs`, `PythonBridge.cs`, `desktop_bridge.py`, `RoleSidebar.xaml(.cs)`
- 不改: `LiteDbLocalStore.cs`, `desktop_bridge.py` 核心聊天逻辑

---

## ADDED Requirements

### Requirement: 推理模型兼容性
The system SHALL 在 `_ensure_client()` 中检测模型名称是否含 `reasoner`/`o1`/`o3`，若是则使用 `instructor.Mode.JSON` 替代 `instructor.Mode.TOOLS`，避免 `Thinking mode does not support tool_choice` 400 错误。

```python
# llm_caller.py L48 修改
_REASONING_MODELS = {"reasoner", "o1", "o3"}

def _is_reasoning_model(model: str) -> bool:
    return any(kw in model.lower() for kw in _REASONING_MODELS)

mode = instructor.Mode.JSON if _is_reasoning_model(current_model) else instructor.Mode.TOOLS
self._client = instructor.apatch(client, mode=mode)
```

#### Scenario: 推理模型正常对话
- **WHEN** 用户在 API 设置中选择 `deepseek-reasoner` 或 `o1-mini` → 发送消息
- **THEN** `instructor` 使用 `Mode.JSON` 发送 → 无 400 报错 → LLM 返回 JSON → 正常解析

### Requirement: 属性面板跟随角色切换
The system SHALL 在 `MainViewModel.OnCurrentRoleChanged` 中自动将 `CurrentRole` 的 10 维属性值同步到属性面板的 Slider 绑定源。

#### 实现方案
`AttributePanel` 的每个 Slider 绑定到 `MainViewModel` 上的 10 个 `[ObservableProperty]`。`OnCurrentRoleChanged` 中遍历 `CurrentRole.Profile` 的 10 个属性逐个赋值。

```csharp
// MainViewModel.cs — OnCurrentRoleChanged 增强
partial void OnCurrentRoleChanged(RoleData? value)
{
    if (value != null)
    {
        // 同步 10 维属性到属性面板绑定
        EducationLevel = value.Profile.EducationLevel;
        RationalEmotional = value.Profile.RationalEmotional;
        // ... 其余 8 个属性
        // ⑨模式触发
        IsCirnoMode = value.Profile.EducationLevel == -100;
    }
    _messagesViewSource.View.Refresh();
    if (value != null && _currentSession != null)
        _currentSession.RoleName = value.Name;
}
```

#### Scenario: 点击角色 → 属性面板更新
- **WHEN** 用户点击侧边栏"傲娇女友"角色
- **THEN** 右侧属性面板所有 Slider 更新为该角色的 10 维属性值（非全 0）

### Requirement: 对话视图角色感知
The system SHALL 在 `ConversationView.xaml` 标题栏显示当前角色名称。格式：`{CurrentSession.Title} · 当前对话：{CurrentRole.Name}`，`CurrentRole` 为空时显示"未指定角色"。

```xml
<!-- ConversationView.xaml 标题栏新增 -->
<StackPanel Orientation="Horizontal">
    <TextBlock Text="{Binding CurrentSession.Title}" FontSize="14" FontWeight="SemiBold"/>
    <TextBlock Text=" · 当前对话：" Foreground="{DynamicResource TextSecondaryBrush}" FontSize="12" VerticalAlignment="Center" Margin="4,0,0,0"/>
    <TextBlock Text="{Binding CurrentRole.Name, TargetNullValue='未指定角色'}" FontSize="12" Foreground="{DynamicResource PrimaryBrush}" FontWeight="SemiBold" VerticalAlignment="Center"/>
</StackPanel>
```

#### Scenario: 切换角色后标题栏更新
- **WHEN** 用户点击侧边栏"知性姐姐"
- **THEN** 对话区标题栏显示"今天的闲聊 · 当前对话：知性姐姐"

### Requirement: ⑨模式修复
The system SHALL 在 `OnCurrentRoleChanged` 中调用 `IsCirnoMode = (role.EducationLevel == -100)`，并在 `OnIsCirnoModeChanged` 中触发 `App.SetTheme(IsCirnoMode)`。

#### Scenario: ⑨模式触发
- **WHEN** 用户选择角色"笨蛋⑨"（EducationLevel=-100）或拖动文化水平滑块至 -100
- **THEN** 全局界面切换为冰蓝色调

#### Scenario: ⑨模式退出
- **WHEN** 用户选择其他角色或拖动文化水平 > -100
- **THEN** 全局界面恢复暖色

### Requirement: API 配置持久化
The system SHALL 在 `PythonBridge.ApplySettings()` 中将 API Key / Base URL / Model 写入 LiteDB 持久化存储，并在启动时从 LiteDB 恢复到 `_runtime_overrides`。

#### 实现
```python
# desktop_bridge.py apply_settings() 增强
def apply_settings(settings_dict: dict) -> None:
    from config import apply_runtime_settings as _apply
    _apply(settings_dict)
    _llm_caller.flush_client()
    # 落盘到 LiteDB（通过 C# 侧调用的 LocalStore）
```

C# 侧：`PythonBridge.ApplySettings()` → `desktop_bridge.apply_settings()` → `LocalStore.SaveSettings(settingsData)`（由 C# 侧调，非 Python 侧写文件）。

#### Scenario: 设置持久化
- **WHEN** 用户填写 API Key / Base URL / 模型 → 保存 → 重启 MISS.exe
- **THEN** 配置从 LiteDB 加载 → 设置面板自动预填

### Requirement: 删除会话
The system SHALL 在侧边栏会话列表中每个会话项右侧显示删除按钮，点击后调用 `DeleteSessionCommand` 从 `Sessions` 集合和 LiteDB 中移除。

```xml
<!-- RoleSidebar.xaml 会话 ListBox ItemTemplate 新增删除按钮 -->
<Button Content="✕" Command="{Binding DataContext.DeleteSessionCommand, RelativeSource={RelativeSource AncestorType=UserControl}}" 
        CommandParameter="{Binding}" Width="20" Height="20" ToolTip="删除会话"/>
```

```csharp
// MainViewModel.cs
[RelayCommand]
private void DeleteSession(SessionData session)
{
    _sessions.Remove(session);
    LocalStore.DeleteSession(session.Id);
    if (_currentSession == session)
        _currentSession = _sessions.FirstOrDefault();
}
```

#### Scenario: 删除会话
- **WHEN** 用户点击"昨天的讨论"右侧 ✕ 按钮 → 确认
- **THEN** 侧边栏移除该会话 → LiteDB 物理删除 → 若该会话是当前选中项则切换到下一个会话
