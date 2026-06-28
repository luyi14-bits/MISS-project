# Checklist

## MVVM 视图模型
- [ ] NuGet: `CommunityToolkit.Mvvm >= 8.2.0` + `LiteDB >= 5.0.0` 已安装
- [ ] `ViewModels/MainViewModel.cs` 继承 `ObservableObject`，全部属性使用 `[ObservableProperty]` 源生成
- [ ] 命令使用 `[RelayCommand]` 绑定（非手写 `ICommand` 类）
- [ ] 属性完整：Sessions / Roles / CurrentSession / CurrentRole / IsInnerThoughtVisible / IsCirnoMode / IsPanelCollapsed
- [ ] `_allMessages` (ObservableCollection) + `_messagesViewSource` (CollectionViewSource) 正确初始化
- [ ] `MainWindow.DataContext = viewModel` 绑定成功
- [ ] **零 Code-Behind 验证**：`*.xaml.cs` 中无 `x:Name` 引用操作 UI 控件、无 `foreach` 遍历 `ObservableCollection` 修改视觉树
- [ ] **跨线程安全**：`MainViewModel` 构造函数调用 `BindingOperations.EnableCollectionSynchronization(_allMessages, new object())`，或所有 `_allMessages.Add()` 调用包裹 `Dispatcher.Invoke()`

## 新增模型
- [ ] `Models/SessionData.cs` 存在，含 `Id`, `Title`, `RoleName`, `CreatedAt`
- [ ] `Controls/ChatMessage.cs` 新增 `IsInnerVisible`（INotifyPropertyChanged）、`Sender` 字段
- [ ] 3 个默认会话："今天的闲聊" / "昨天的讨论" / "属性调试"

## 侧边栏 — 会话区
- [ ] 侧边栏上方显示"会话"标题 + "+ 新建"按钮
- [ ] 会话 ListBox `ItemsSource="{Binding Sessions}"` 绑定
- [ ] 点击"+ 新建" → 新会话出现 → 对话区清空
- [ ] 点击已有会话 → 切换对话区内容
- [ ] 当前选中会话高亮

## 侧边栏 — 折叠/展开
- [ ] « / » 按钮切换 Width 200px ↔ 38px
- [ ] 折叠态竖排标签可见，ContextMenu 可用

## CollectionViewSource 角色过滤
- [ ] 点击角色 → `CollectionViewSource.Filter` 只放行匹配消息（零 .ToList() 拷贝）
- [ ] 用户消息（IsUser=true）始终显示
- [ ] 未绑定角色的会话显示全部消息
- [ ] **性能验证**：500+ 条消息会话中切换角色 → 界面 < 16ms 刷新

## 后端上下文过滤 + Token 截断
- [ ] `BuildContextMessages()` 第一层：角色绝对隔离（LINQ Where RoleName）
- [ ] `BuildContextMessages()` 第二层：`Microsoft.ML.Tokenizers.Tokenizer.CreateTiktokenForModel("gpt-4").Encode()` 真实 Token 累计截断（**禁止**字符除法估算）
- [ ] 选择角色"傲娇女友"后发送 → 后端上下文不含其他角色消息
- [ ] 同角色对话 Token 超限 → 早期消息被截断

## Python 桥接边界防御
- [ ] `desktop_bridge.py` 中 `BridgeProfile(BaseModel)` 定义完整 10 维属性 + `ge/le` 范围校验
- [ ] `_validate_profile(profile_dict)` → `BridgeProfile(**profile_dict)` 强校验入口
- [ ] `chat()` 顶层 try/except → 返回 `{"_error": True, "message": "..."}` 异常透传
- [ ] `chat_stream()` 使用 `queue.Queue(maxsize=100)` + `threading.Event` 熔断
- [ ] `q.get(timeout=1.0)` 防死锁 + `finally: stop_event.set(); t.join(2.0)` 线程回收
- [ ] **非法 profile 测试**：C# 传 `{"rational_emotional": 999}` → Python 返回 `{"_error": True, ...}`（不崩溃）

## LLM 结构化输出（instructor + pydantic）
- [ ] `pip install instructor` 成功
- [ ] `llm_caller.py` 中 `ChatResponse(BaseModel)` 定义 `inner_thought` + `spoken`（含 Field description）
- [ ] `_ensure_client()` 使用 `instructor.apatch(AsyncOpenAI(...))`
- [ ] `call()` 使用 `response_model=ChatResponse, max_retries=2`
- [ ] `analyze_character()` 使用 `response_model=AnalysisResult`
- [ ] 所有 `re.search` / `_strip_markdown` / `SpokenStreamParser` 已删除
- [ ] Schema 不匹配 → `instructor` 自动重试 2 次 → 仍失败抛 `RuntimeError`（无 `{"spoken": "抱歉报错了"}` 脏数据）

## Trinity 导师审计修复项
- [ ] **SpokenStreamParser 已删除**：`llm_caller.py` 中不再存在 `class SpokenStreamParser`（原 L9-L111 共 116 行）
- [ ] **stream() 精简**：`stream()` 方法改为纯 token 透传 + 最终 `_parse_json_response(full_text)` 一次性校验
- [ ] **_parse_json_response 精简**：只保留 `_try_strict_json` → `_normalize` 一条路径；`_try_regex_extract`、`_strip_markdown_code_block`、`_clean_raw_text` 三条 fallback 已删除
- [ ] **_dict_to_profile 零信任**：`desktop_bridge.py` L112 替换为 `MISSProfile(**d)` 强校验（非 `.get("key", 0)` 静默默认值）
- [ ] **analyze_character 修复**：`desktop_bridge.py` L276 的 `re.search(r"\{[^}]+\}", spoken)` 已删除，改为 instructor 自动解析

## LiteDB 持久化
- [ ] `ILocalStore.SaveSessions/LoadSessions` 正确读写 `%APPDATA%/MISS/miss.db`（LiteDB BsonDocument）
- [ ] `SessionData` + `ChatMessage` 模型具无参构造函数 + 公开 get/set 属性（LiteDB BsonMapper 原生映射，**禁止**中转 `JsonSerializer`）
- [ ] 发送消息 → 300ms 防抖保存
- [ ] 新建/切换/删除会话 → 立即保存
- [ ] **重启恢复**：关闭重开 → 所有会话和消息历史完整恢复 → 选中上次关闭的会话
- [ ] `ChatMessage` 往返序列化正确（所有字段存入 LiteDB 后读回不丢失）
- [ ] `ChatMessage` JSON 序列化/反序列化正确（所有字段往返不丢失）

## 对话标题栏
- [ ] 顶部显示 `{Binding CurrentSession.Title}`
- [ ] ⚙ 设置按钮在标题栏右侧

## ⑨模式主题
- [ ] 选择"笨蛋⑨" → 冰蓝主题 + 徽章显示
- [ ] `education_level == -100` → 冰蓝 / `> -100` → 暖色
- [ ] **死角审计**：会话列表 ItemTemplate → DynamicResource
- [ ] **死角审计**：角色列表 ItemTemplate → DynamicResource
- [ ] **死角审计**：消息气泡 DataTemplate → DynamicResource
- [ ] **死角审计**：动态控件 → Application.Current.Resources 取色
- [ ] **死角审计**：⑨模式下新建会话 → 新项冰蓝渲染

## 内心独白开关
- [ ] CheckBox `{Binding IsInnerThoughtVisible}` 绑定
- [ ] 勾选 → 所有历史 inner_thought 展开
- [ ] 取消 → 所有折叠
- [ ] 新消息跟随开关状态
- [ ] **滚动平滑**：100+ 条消息切换 → 无跳动

## 属性面板折叠修复
- [ ] 旧 CollapseBtn 已移除
- [ ] ToggleButton 在 MainWindow 层级常驻
- [ ] 折叠/展开后按钮始终可点击

## 集成测试
- [ ] 双击 MISS.exe → 主窗口 1100×750 → 侧边栏含 3 个默认会话 + 4 个内置角色
- [ ] 新建会话 → 输入消息 → 切换回"今天的闲聊"→ 消息仍在
- [ ] 选择"笨蛋⑨"→ 冰蓝主题 → 选择其他 → 暖色恢复
- [ ] 勾选内心独白 → 展开 → 滚动无跳动
- [ ] 折叠→展开属性面板 → 无异常
- [ ] **重启恢复**：关闭 → 重开 → 所有会话和消息完整存在
