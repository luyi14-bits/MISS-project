# Tasks

- [ ] Task 0: MVVM 视图模型层（CommunityToolkit.Mvvm，先于所有 UI 任务）
  - [ ] SubTask 0.1: NuGet 安装 `CommunityToolkit.Mvvm`（`>= 8.2.0`）+ `LiteDB`（`>= 5.0.0`）
  - [ ] SubTask 0.2: 创建 `ViewModels/MainViewModel.cs`，继承 `ObservableObject`
    - 使用 `[ObservableProperty]` 声明：`_sessions`, `_roles`, `_currentSession`, `_currentRole`, `_isInnerThoughtVisible`, `_isCirnoMode`, `_isPanelCollapsed`
    - `_allMessages`: `ObservableCollection<ChatMessage>` → `_messagesViewSource` (CollectionViewSource)
    - `[RelayCommand]`：`CreateSession`, `DeleteSession`, `ToggleInnerThought`, `SendMessage`

  - [ ] SubTask 0.2: `MainViewModel` 构造函数中初始化 CollectionViewSource：
    - `_messagesViewSource.Source = _allMessages`
    - `CurrentRole` setter 中调用 `ApplyRoleFilter(roleName)`
  - [ ] SubTask 0.3: 确保 `MainViewModel` 为单例（`App.xaml.cs` 中创建，`Application.Current.Properties["ViewModel"]` 或 `App.Current.MainViewModel` 静态属性访问）
  - [ ] SubTask 0.4: `MainWindow.DataContext = viewModel`，所有控件绑定到 ViewModel 属性

- [ ] Task 1: 新增 SessionData 模型 + 消息模型增强
  - [ ] SubTask 1.1: 创建 `Models/SessionData.cs`：`Id`, `Title`, `RoleName`, `CreatedAt`
  - [ ] SubTask 1.2: 修改 `Controls/ChatMessage.cs`：新增 `IsInnerVisible` 属性（`INotifyPropertyChanged`）、`Sender` 字段（记录角色名）
  - [ ] SubTask 1.3: 在 `MainViewModel.LoadSessions()` 中创建 3 个默认会话："今天的闲聊"、"昨天的讨论"、"属性调试"

- [ ] Task 2: 侧边栏改造 — 新增会话区 + 折叠功能
  - [ ] SubTask 2.1: 修改 `RoleSidebar.xaml`：在现有"角色"区域上方增加"会话"区域
    - 会话区头部：`<TextBlock>会话</TextBlock>` + `Button "+ 新建"`
    - 会话列表：`ListBox ItemsSource="{Binding Sessions}"`，每项显示标题
    - 会话项与角色项之间用分割线隔开
    - 会话项选中态绑定：`ListBox.SelectedItem="{Binding CurrentSession, Mode=TwoWay}"`
  - [ ] SubTask 2.2: 修改 `RoleSidebar.xaml.cs`：
    - `CreateSession_Click()`：新建 SessionData → `ViewModel.Sessions.Add(session)` → `ViewModel.CurrentSession = session` → 触发防抖保存
    - 删除 `RoleListBox.SelectionChanged` 事件中的旧逻辑 → 改为绑定 `CurrentRole`
  - [ ] SubTask 2.3: 新增侧边栏折叠按钮：
    - 绑定 `IsChecked` 到 `MainViewModel.IsPanelCollapsed`（或直接 code-behind 切换 Width）
    - 折叠/展开时侧边栏 Width 切换 200px ↔ 38px
  - [ ] SubTask 2.4: 确保角色右键菜单（导出/导入/删除）在折叠态仍可通过 ContextMenu 访问

- [ ] Task 3: 对话视图 — CollectionViewSource 过滤 + 会话切换 + 上下文截断
  - [ ] SubTask 3.1: `ConversationView.xaml.cs` 重写 `SendMessage()`：
    - 用 `BuildContextMessages()` 构造发给后端的上下文（两层裁剪：角色隔离 + 滑动窗口截断 20 轮）
    - 发送后追加消息到 `ViewModel._allMessages` → 触发 `CollectionViewSource` 自动刷新界面
    - 调用 `ViewModel.DebouncedSaveSessions()` 防抖持久化
  - [ ] SubTask 3.2: `ApplyRole()` 方法改造：
    - 设 `ViewModel.CurrentRole = role` → `CollectionViewSource.Filter` 自动生效
    - 设 `ViewModel.CurrentSession.RoleName = role.Name`
  - [ ] SubTask 3.3: `SwitchSession()` 改造：
    - 保存当前会话消息到 SessionData
    - 加载目标会话消息到 `_allMessages` → `CollectionViewSource.View.Refresh()`
  - [ ] SubTask 3.4: **渲染死角审计**：确保 `ConversationView.xaml` 中消息气泡 DataTemplate 全部使用 `DynamicResource`
  - [ ] SubTask 3.5: **Python 桥接边界防御**：修改 `desktop_bridge.py`（或创建独立 `desktop_bridge_pydantic.py`）
    - `_validate_profile(profile_dict)` → `BridgeProfile(**profile_dict)` 强校验 + `ge/le` 范围拦截
    - `chat()` 顶层 try/except → 返回 `{"_error": True, "message": "..."}` 而不是抛异常
    - `chat_stream()` 用 `queue.Queue(maxsize=100)` + `threading.Event` 熔断 + `q.get(timeout=1.0)` 防死锁
    - finally 分支 `stop_event.set()` + `t.join(timeout=2.0)` 强制回收线程
    - 异常透传：`{"_error": True, "message": "..."}` 序列化到队列（统一使用 `_error`，非 `type`）

- [ ] Task 3.6: **Python 侧 pydantic 校验模型创建**
  - [ ] SubTask 3.6.1: 在 `miss-backend/services/desktop_bridge.py` 中定义 `BridgeProfile(BaseModel)`，覆盖全部 10 维属性 + `ge/le` 范围校验
  - [ ] SubTask 3.6.2: 确保 `from services.desktop_bridge import BridgeProfile` 在嵌入式 Python 环境中可导入成功

- [ ] Task 3.7: **Python 侧 llm_caller.py 重构（instructor + pydantic）**
  - [ ] SubTask 3.7.1: NuGet / pip：`pip install instructor pydantic`
  - [ ] SubTask 3.7.2: 修改 `services/llm_caller.py`：
    - 定义 `ChatResponse(BaseModel)`：`inner_thought` + `spoken`（含 Field description）
    - `_ensure_client()` 改为 `instructor.apatch(AsyncOpenAI(...))`
    - `call()` 改为 `response_model=ChatResponse, max_retries=2`
    - `analyze_character()` 改为 `response_model=AnalysisResult`
    - 删除所有 `re.search` / `_strip_markdown` / `SpokenStreamParser` 逻辑
  - [ ] SubTask 3.7.3: 验证：`python -c "from services.llm_caller import LLMCaller; print('import OK')"`

- [ ] Task 3.8: **删除 SpokenStreamParser + 精简 stream()**
  - [ ] SubTask 3.8.1: 删除 `llm_caller.py` L9-L111 整个 `SpokenStreamParser` 类（116 行）
  - [ ] SubTask 3.8.2: 精简 `stream()` L197-243：去掉 `SpokenStreamParser` 相关代码，改为纯 token 透传 + 最终 `_parse_json_response(full_text)` 一次性校验
  - [ ] SubTask 3.8.3: 删除 `llm_caller.py` 中所有 `_try_regex_extract` / `_strip_markdown_code_block` / `_clean_raw_text` 三条 fallback。只保留 `_try_strict_json` → `_normalize` 一条路径。`_parse_json_response` 目标行数从 27 行精简到 ~8 行

- [ ] Task 3.9: **修复 `_dict_to_profile` 零信任输入**
  - [ ] SubTask 3.9.1: `desktop_bridge.py` L112-125：将 `d.get("rational_emotional", 0)` 等 10 个 `.get()` 调用替换为 `MISSProfile(**d)` 强校验
  - [ ] SubTask 3.9.2: 加 try/except ValueError → 返回 `{"_error": True, "message": f"C# 传入的角色属性字典校验失败: {str(e)}"}`
  - [ ] SubTask 3.9.3: 确保 `chat_stream()` L205 的 `except Exception: pass` 改为显式异常透传：`q.put(json.dumps({"_error": True, "message": str(e)}))`（统一使用 `_error` 字段，非 `type` 字段）

- [ ] Task 3.10: **修复 `analyze_character` 手写正则**
  - [ ] SubTask 3.10.1: `desktop_bridge.py` L272-293：删除 `re.search(r"\{[^}]+\}", spoken)` 手写 JSON 提取
  - [ ] SubTask 3.10.2: 改为通过 `LLMCaller.call()` 调用 + `instructor` `AnalysisResult` Pydantic 模型解析 → 返回 10 维属性 dict

- [ ] Task 4: ⑨模式主题联动
  - [ ] SubTask 4.1: 修改 `Resources/Styles.xaml`：Normal + Cirno 两套色板
  - [ ] SubTask 4.2: 修改 `App.xaml.cs`：`SetTheme(bool isCirno)` 替换 `Application.Current.Resources` 中所有颜色刷子
  - [ ] SubTask 4.3: ⑨模式触发点：`AttributePanel.Slider_ValueChanged` 中 `education_level == -100` → `ViewModel.IsCirnoMode = true` → `App.SetTheme(true)`
  - [ ] SubTask 4.4: 属性面板顶部新增 CirnoBadge（绑定 `ViewModel.IsCirnoMode` → Visibility）
  - [ ] SubTask 4.5: **渲染死角审计**：逐文件 grep 排查 `Foreground="#"` / `new SolidColorBrush` / `{StaticResource` → 全部改为 `DynamicResource`

- [ ] Task 5: 内心独白全局开关（MVVM 方式）
  - [ ] SubTask 5.1: `ConversationView.xaml` 工具栏新增 `CheckBox IsChecked="{Binding IsInnerThoughtVisible}"`
  - [ ] SubTask 5.2: `MainViewModel.IsInnerThoughtVisible` setter 中遍历 `_allMessages.Where(m => !m.IsUser)` 设置 `IsInnerVisible`
  - [ ] SubTask 5.3: 消息 DataTemplate 中 `InnerBorder.Visibility` 绑定 `IsInnerVisible`
  - [ ] SubTask 5.4: **滚动平滑处理**：批量操作期间标志 + `Dispatcher.BeginInvoke(ScrollToEnd, DispatcherPriority.Loaded)`

- [ ] Task 6: 属性面板折叠修复
  - [ ] SubTask 6.1: `MainWindow.xaml` Grid.Column="2" 改为 ToggleButton + AttributePanel 嵌套
  - [ ] SubTask 6.2: ToggleButton `Click` → 切换 `ViewModel.IsPanelCollapsed` → `AttributePanelView.Visibility`
  - [ ] SubTask 6.3: 移除 `AttributePanel.xaml` 中旧 `CollapseBtn`

- [ ] Task 7: LiteDB 持久化
  - [ ] SubTask 7.1: 修改 `LocalStore.cs`：新增 `SaveSessions(List<SessionData>)` / `LoadSessions()`
    - 文件路径：`%APPDATA%/MISS/miss.db`（LiteDB 单文件数据库）
    - 确保 `SessionData` 和 `ChatMessage` 模型具备无参构造函数 + 公开 get/set 属性（LiteDB `BsonMapper` 原生映射要求，**禁止**手动调用 `JsonSerializer` 做 JSON 字符串中转）
  - [ ] SubTask 7.2: 在 `MainViewModel.cs` 中实现 `DebouncedSaveSessions()`（300ms CancellationTokenSource 防抖）
  - [ ] SubTask 7.3: 触发时机：
    - `SendMessage()` 成功后调 `DebouncedSaveSessions()`
    - `CreateSession_Click()` 后立即调 `SaveSessions()`
    - `SwitchSession()` 时立即调 `SaveSessions()`
  - [ ] SubTask 7.4: 启动时 `MainViewModel.LoadSessions()` → 从 `LocalStore.LoadSessions()` 恢复所有会话 → 选中上次关闭的会话

- [ ] Task 8: 对话标题栏
  - [ ] SubTask 8.1: `ConversationView.xaml` 顶部：
    - `TextBlock Text="{Binding CurrentSession.Title}"` 显示会话名
    - ⚙ 设置按钮移至标题栏右侧
  - [ ] SubTask 8.2: `MainViewModel.CurrentSession` setter 中更新标题

# Task Dependencies
- **Task 0 必须先做**（MVVM + NuGet 依赖是所有 UI 任务的基础）
- Task 1 依赖 Task 0
- Task 2 依赖 Task 0 + 1
- Task 3 依赖 Task 0 + 1 + 2
- Task 3.6 / 3.7 / 3.8 / 3.9 / 3.10 可并行于 Task 4-6（Python 侧改动不影响 WPF UI）
- Task 4 可并行于 Task 1-3
- Task 5 依赖 Task 0 + 3（ViewModel 就绪 + 对话区就绪）
- Task 6 可并行
- Task 7 依赖 Task 0 + 1
- Task 8 依赖 Task 0 + 3

# 技术要点
- **CommunityToolkit.Mvvm**：`[ObservableProperty]` 源生成器自动生成 `public` 属性 + `OnXxxChanged` 钩子；`[RelayCommand]` 自动生成 `ICommand` 绑定
- **跨线程安全**：`MainViewModel` 构造函数中调用 `BindingOperations.EnableCollectionSynchronization(_allMessages, new object())` 启用跨线程同步；或所有后台线程对 `ObservableCollection` 的写入通过 `Application.Current.Dispatcher.Invoke()` 调度。**禁止**后台线程直接 `.Add()`。
- **LiteDB**：单例 `LiteDatabase("Filename=%APPDATA%/MISS/miss.db")`，所有 `Insert`/`Update`/`Delete` 在 `Task.Run()` 内执行
- **CollectionViewSource**：不修改底层集合，仅拦截 View 层 Filter 谓词 → 零内存拷贝
- **Token 截断**：`MAX_TOKEN_LIMIT = 2048`，C# 侧使用 `Microsoft.ML.Tokenizers.Tokenizer.CreateTiktokenForModel("gpt-4")` 做真实 Token 编码累计，**禁止**字符长度除法估算
- **instructor**：`instructor.apatch(client)` → `response_model=ChatResponse, max_retries=2` → 彻底废除正则解析
- **流式熔断**：`queue.Queue(maxsize=100)` + `threading.Event` + `q.get(timeout=1.0)` → 防 OOM + 防死锁
- **异常透传**：Python 侧所有异常统一序列化为 `{"_error": True, "message": "..."}`（`_error` 是 C# 侧判断成功的唯一 Boolean 字段，**禁止**使用 `type` 等其他字段名）
