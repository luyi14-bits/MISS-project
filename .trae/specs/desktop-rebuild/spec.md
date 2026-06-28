# WPF Demo 重构 Spec — MVVM 架构 + 会话管理 + 性能防劣化

## Why
当前 WPF demo 存在 6 个核心缺陷，与网页版体验差距明显：
1. 没有会话管理——无法新建对话、切换"今天的闲聊/昨天的讨论/属性调试"
2. 左边角色栏没有折叠/展开功能（网页版有 sidebarToggle）
3. 点击角色后对话区不隔离——应该只显示当前角色的对话历史
4. 没有⑨模式主题切换——当 `education_level == -100` 时无冰蓝主题联动
5. 没有内心独白全局开关——无法一键显示/隐藏所有 inner_thought
6. 属性面板折叠按钮点击后无法恢复——布局 Bug

## 技术栈与开发红线

| 层级 | 强制技术 | 禁止 |
|------|---------|------|
| MVVM | `CommunityToolkit.Mvvm`（`[ObservableProperty]` / `[RelayCommand]` 源生成器） | **禁止**手写 `INotifyPropertyChanged` 样板、禁止 `Fody` / `Prism` 等替代方案 |
| 持久化 | `LiteDB` 无 SQL 文档型数据库 | **禁止** SQLite 直连、**禁止** Entity Framework |
| 异步 | `Task.Run` + `async/await` + `Dispatcher.BeginInvoke` | **禁止** `ConfigureAwait(false).GetAwaiter().GetResult()` 死锁模式 |
| Token 计量 | `tiktoken`（Python）/ `Microsoft.ML.Tokenizers`（C#） | **禁止**按轮数/字符数粗糙截断 |
| LLM 结构化输出 | `pydantic` + `instructor`（Python 侧接管 OpenAI 客户端） | **禁止**手写 `re.search` JSON 提取、**禁止** `SpokenStreamParser` 状态机 |
| Python 桥接边界 | `pydantic` 强类型校验入口 + `queue.Queue(maxsize=100)` + `threading.Event` 熔断 | **禁止** `except Exception: pass`、**禁止**裸 `dict.get()` 绕过校验 |

### 开发红线（编译级约束）
1. **零 Code-Behind 逻辑**：所有业务逻辑（新建会话、切换角色、内心独白批量切换、持久化读/写）必须在 `ViewModel` 中通过 `[RelayCommand]` 驱动。`*.xaml.cs` 中**禁止**出现任何 `x:Name` 引用操作 UI 控件、**禁止** `foreach` 遍历 `ObservableCollection` 修改 UI 视觉树。
2. **UI 虚拟化防护**：消息列表展开/折叠内心独白时，必须仅通过改变绑定的 `ViewModel.IsInnerVisible` 属性驱动界面刷新。**禁止** `foreach` 遍历 `ItemsControl` 子元素直接操作 WPF 视觉树。
3. **线程隔离异步落盘**：所有 `LiteDB` 的 `Insert`/`Update`/`Delete` 事务必须通过 `Task.Run` 封装在后台工作线程执行。**禁止**在 UI 线程执行任何磁盘 I/O。
4. **跨线程 ObservableCollection 安全**：所有后台线程（`Task.Run`、`Thread`、`BlockingCollection` 消费者）对 `ObservableCollection` 的增删操作**必须**通过 `Application.Current.Dispatcher.Invoke(() => _allMessages.Add(msg))` 调度到 UI 线程。或在 `MainViewModel` 构造函数中调用 `BindingOperations.EnableCollectionSynchronization(_allMessages, _lockObject)` 启用跨线程同步。**禁止**后台线程直接 `_allMessages.Add()`——这会触发 `InvalidOperationException: Cannot change ObservableCollection on a different Dispatcher thread`。
5. **严格上下文隔离**：组装给 LLM 的 `messages` 列表时，提供基于当前 `RoleName` 的绝对过滤逻辑。如果当前是"笨蛋⑨"会话，上下文中**禁止**出现任何一行属于"知性姐姐"的历史对话。
6. **禁止裸写正则解析**：删除 `llm_caller.py` 中所有手写 JSON 提取逻辑（`re.search` fallback、`_strip_markdown` 等）、删除 `SpokenStreamParser`。Python 侧 LLM 调用统一由 `instructor` + `pydantic` 接管。
7. **禁止静默失败**：LLM 输出不符合 Pydantic Schema → `instructor` 自动重试（最多 2 次）→ 仍失败则抛 `RuntimeError`。**禁止**返回 `{"spoken": "抱歉报错了"}` 伪装成正常回复。
8. **Python 侧零信任输入与异常透传**：`desktop_bridge.py` 接收 C# 传入的 `profile_dict` → 立即 `MISSProfile(**profile_dict)` 强校验。Python 侧所有异常（包括流式）统一使用 `{"_error": True, "message": "..."}` 单一格式回传 C#。`_error` 是 C# 桥接层判断是否成功的唯一 Boolean 字段。**禁止**使用 `{"type": "error", ...}` 等其他格式、**禁止** `except Exception: pass` 或 `return ""` 吞噬异常。
9. **删除 SpokenStreamParser 状态机**：`llm_caller.py` L9-L111 的 116 行手写流式解析器必须删除。`stream()` 方法 L197-243 已通过 `full_text` 收集 + `_parse_json_response()` 全量解析覆盖了它的功能——两套逻辑冗余。流式只需透传 token，最终用 `instructor` + `pydantic` 校验完整 JSON。
10. **删除四条 JSON fallback 路径**：`_parse_json_response` L245-271 中的 `_try_regex_extract`、`_strip_markdown_code_block`、`_clean_raw_text` 三条 fallback 必须删除。保留一条 `_try_strict_json` 对 OpenAI 原生 `response_format={"type":"json_object"}` 的容错足够。如果模型不能输出合法 JSON，应该报错而不是静默降级为原文。
11. **修复 `analyze_character` 手写正则**：`desktop_bridge.py` L272-293 的 `re.search(r"\{[^}]+\}", spoken)` 必须在 instructor 方案实施后删除，改为 `_llm_caller.call()` → `instructor` 的 `AnalysisResult` 模型自动解析。

## What Changes
- **MVVM 架构升级**：`CommunityToolkit.Mvvm` 源生成器替代手写 `INotifyPropertyChanged`，核心状态集中到 `ViewModels/`
- **LiteDB 持久化**：替代 JSON 文件读写方案。会话快照 + 消息集合以 BSON 文档存入 `%APPDATA%/MISS/miss.db`（LiteDB 单文件数据库），所有读写通过 `ILocalStore` 接口异步执行
- 侧边栏新增"会话"区域（会话列表 + 新建按钮），在"角色"区域上方
- 会话数据结构：`SessionData` + `ChatMessage`，均继承 `ObservableObject`，使用 `LiteDB` BsonId 映射
- 角色过滤改用 `CollectionViewSource` 视图层拦截（避免 LINQ 全量拷贝）
- ⑨模式主题联动：`education_level == -100` → 全局 DynamicResource 冰蓝切换
- 内心独白全局开关：`[RelayCommand] ToggleInnerThought` → `Task.Run` 批量更新 → `Dispatcher.BeginInvoke` ScrollToEnd
- 属性面板折叠修复：手柄移至 `MainWindow` 层级
- 后端上下文滑动窗口截断 + 角色隔离过滤

## Impact
- **新增**：`ViewModels/MainViewModel.cs`, `ViewModels/ConversationViewModel.cs`, `Models/SessionData.cs`, `Services/ILocalStore.cs`, `Services/LiteDbLocalStore.cs`
- **修改**：`Controls/ChatMessage.cs`（迁移至 CommunityToolkit.Mvvm）, `Views/*.xaml(.cs)`, `MainWindow.xaml(.cs)`, `App.xaml.cs`
- **删除**：`Services/LocalStore.cs`（JSON → LiteDB）、`LocalStore.cs` 中 sessions 相关逻辑
- **复用**：`PythonBridge.cs`（或 ApiClient）、`MISSProfile.cs`、`ChatResponse.cs`

---

## ADDED Requirements

### Requirement: MVVM 视图模型层（CommunityToolkit.Mvvm 源生成器）
The system SHALL 使用 `CommunityToolkit.Mvvm` 替代手写 `INotifyPropertyChanged`。所有 ViewModel 属性通过 `[ObservableProperty]` 源生成，命令通过 `[RelayCommand]` 绑定。**禁止**手写 `OnPropertyChanged()` 样板。

#### 视图模型结构
```csharp
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;

namespace MISS.ViewModels
{
    public partial class MainViewModel : ObservableObject
    {
        [ObservableProperty]
        private ObservableCollection<SessionData> _sessions = new();

        [ObservableProperty]
        private ObservableCollection<RoleData> _roles = new();

        [ObservableProperty]
        private SessionData? _currentSession;

        [ObservableProperty]
        private RoleData? _currentRole;

        [ObservableProperty]
        private bool _isInnerThoughtVisible;

        [ObservableProperty]
        private bool _isCirnoMode;

        [ObservableProperty]
        private bool _isPanelCollapsed;

        // _allMessages + _messagesViewSource (CollectionViewSource) 不变
    }
}
```

#### Scenario: 内心独白切换（MVVM 方式）
- **WHEN** 用户勾选"内心独白" CheckBox
- **THEN** `MainViewModel.IsInnerThoughtVisible = true` → 所有绑定到此属性的 `ChatMessage.IsInnerVisible` 自动联动 → 无需 code-behind 遍历集合

#### Scenario: 角色选择（MVVM 方式）
- **WHEN** 用户点击侧边栏角色
- **THEN** `MainViewModel.CurrentRole = role` → `CollectionViewSource` 自动过滤对话区消息 → 无需 code-behind 操作

### Requirement: CollectionViewSource 角色过滤（性能优化）
The system SHALL 使用 WPF `CollectionViewSource` 进行角色过滤，替代 LINQ 全量 `.Where().ToList()`。

#### 为什么不用 LINQ
LINQ `.Where().ToList()` 每次触发都会创建新的内存副本。当 `_allMessages` 超过 500 条时，频繁切换角色会导致显著的 GC 压力和 UI 延迟。

#### 实现方案
```csharp
// MainViewModel.cs
private readonly CollectionViewSource _messagesViewSource = new();

public ICollectionView MessagesView => _messagesViewSource.View;

// 初始化：将底层集合绑定到 CollectionViewSource
_messagesViewSource.Source = _allMessages;

// 角色切换时：仅修改 Filter 谓词，零内存拷贝
public void ApplyRoleFilter(string? roleName)
{
    _messagesViewSource.View.Filter = msg =>
    {
        if (msg is not ChatMessage m) return true;
        if (m.IsUser) return true;
        if (string.IsNullOrEmpty(roleName)) return true;
        return m.Sender == roleName;
    };
}
```

#### Scenario: 角色过滤性能
- **WHEN** 用户在 500+ 条消息的会话中切换角色
- **THEN** 界面在 16ms 内完成过滤刷新（无 .ToList() 拷贝开销）

### Requirement: 会话管理（新增）
The system SHALL 在左侧角色栏上方新增"会话"区域，支持多会话创建与切换。

#### 数据模型：SessionData
```csharp
public class SessionData
{
    public string Id { get; set; } = Guid.NewGuid().ToString();
    public string Title { get; set; } = "新对话";
    public string RoleName { get; set; } = "";  // 空表示不限角色
    public DateTime CreatedAt { get; set; } = DateTime.Now;
}
```

#### Scenario: 默认会话
- **WHEN** 程序首次启动
- **THEN** 自动创建 3 个预设会话："今天的闲聊"、"昨天的讨论"、"属性调试"，每个会话独立存储消息列表

#### Scenario: 新建会话
- **WHEN** 用户点击侧边栏"会话"区域的 "+ 新建"按钮
- **THEN** 创建新 SessionData（Title="新对话"），会话列表追加新项并自动选中，对话区清空显示空状态

#### Scenario: 切换会话
- **WHEN** 用户点击侧边栏中的某个会话项
- **THEN** 该会话高亮，对话区加载该会话的消息历史，标题栏更新为会话 Title

#### Scenario: 角色过滤
- **WHEN** 用户点击侧边栏"角色"区域的某个角色
- **THEN** 当前会话绑定该角色（SessionData.RoleName = role.Name），`CollectionViewSource.Filter` 只放行 `IsUser=true` 或 `Sender == role.Name` 的消息，新建会话时默认绑定当前会话绑定的角色

### Requirement: 后端上下文过滤 + Token 精确截断
The system SHALL 在向 Python 后端发送消息时，执行两层裁剪：(1) 角色绝对隔离；(2) 基于真实 Token 消耗的滑动窗口。

#### C# 侧 Token 精确截断（`Microsoft.ML.Tokenizers`，强制）
```csharp
// ConversationViewModel.cs — BuildContextMessages()
private const int MAX_TOKEN_LIMIT = 2048;
private static Tokenizer _tokenizer = Tokenizer.CreateTiktokenForModel("gpt-4");

private List<ChatMessage> BuildContextMessages()
{
    // 第一层：角色绝对隔离
    var validHistory = _allMessages
        .Where(m => m.IsUser
            || string.IsNullOrEmpty(CurrentSession.RoleName)
            || m.Sender == CurrentSession.RoleName)
        .OrderByDescending(m => m.Timestamp)
        .Reverse()
        .ToList();

    // 第二层：Tokenizer 精确累计截断
    int tokenCount = 0;
    var result = new List<ChatMessage>();
    for (int i = validHistory.Count - 1; i >= 0; i--)
    {
        var msg = validHistory[i];
        // 将消息内容 encode 为真实 Token 数
        int msgTokens = _tokenizer.Encode(msg.Spoken + msg.InnerThought).Count;
        if (tokenCount + msgTokens > MAX_TOKEN_LIMIT)
            break;
        tokenCount += msgTokens;
        result.Insert(0, msg);
    }

    return result;
}
```

**禁止使用字符/字符串长度除法作为 Token 估算。**`(Spoken+InnerThought).Length / 2` 对中文/CJK 字符的估算误差高达 3-4 倍。必须使用 `Microsoft.ML.Tokenizers` 调用 `o200k_base` 编码器做真实 Token 计数。

**截断原因**：
- **LLM 注意力保护**：上下文 > 2048 Token → 早期对话的角色语气漂移到当前回复
- **防止 OOM**：避免 ChromaDB + 上下文膨胀导致 Python 侧内存溢出
- **序列化开销**：C# → Python 跨进程 JSON 序列化大小与 Token 数线性相关

##### Scenario: 长对话 Token 截断
- **WHEN** 同角色对话累计超过 2048 Token
- **THEN** 发给后端的消息列表从最新消息倒推累加，超出部分自动截断

### Requirement: LLM 结构化输出（instructor + pydantic）
The system SHALL 用 `instructor` 库接管 `llm_caller.py` 的 OpenAI 客户端，通过 Pydantic Schema 强制约束 LLM 输出格式。**禁止**手写正则解析、**禁止** `SpokenStreamParser` 状态机。

#### Python 侧实现（`llm_caller.py` 重构）
```python
import instructor
from pydantic import BaseModel, Field
from openai import AsyncOpenAI

class ChatResponse(BaseModel):
    inner_thought: str = Field(
        description="角色的内心独白，绝对不能留空。如果没有特殊想法也要写符合角色性格的心理活动"
    )
    spoken: str = Field(
        description="角色实际说出口的话，必须直接输出内容，不要包含格式化标签或 markdown"
    )

class AnalysisResult(BaseModel):
    profile: dict[str, int] = Field(
        description="10 维属性值，键为 snake_case 属性名，值为 -100~100 的整数"
    )

class LLMCaller:
    def __init__(self):
        self._client = None

    def _ensure_client(self):
        if self._client is not None:
            return
        from config import get_api_key, get_base_url
        key = get_api_key()
        if not key or key == "sk-placeholder":
            raise RuntimeError("API Key 未配置")
        base = get_base_url()
        client = AsyncOpenAI(api_key=key, base_url=base) if base else AsyncOpenAI(api_key=key)
        self._client = instructor.apatch(client)

    async def call(self, messages: list[dict]) -> dict:
        self._ensure_client()
        try:
            response: ChatResponse = await self._client.chat.completions.create(
                model=get_model() or "gpt-4o",
                messages=messages,
                response_model=ChatResponse,
                max_retries=2,
            )
            return response.model_dump()
        except Exception as e:
            raise RuntimeError(f"LLM 结构化生成或校验失败: {str(e)}")

    async def analyze_character(self, description: str) -> dict:
        self._ensure_client()
        # ... instructor 调 AnalysisResult
```

##### Scenario: Schema 不匹配自动重试
- **WHEN** LLM 返回的 JSON 缺少 `inner_thought` 字段或类型错误
- **THEN** `instructor` 自动重试（最多 2 次）→ 仍失败抛 `RuntimeError` → C# `PythonBridge` 捕获后显式报错

##### Scenario: 流式输出
- **WHEN** 使用流式模式 `POST /api/chat/stream`
- **THEN** `instructor.Partial[ChatResponse]` 逐 token 产出增量 → SSE 透传到前端 → `type: done` 时前端做完整 JSON 校验

### Requirement: Python 桥接边界防御（Pydantic + GIL 安全 + 流式熔断）
The system SHALL 在 `desktop_bridge.py` 中实现三道防线：

#### 第一道：Pydantic 强类型校验入口
```python
from pydantic import BaseModel, Field

class BridgeProfile(BaseModel):
    rational_emotional: int = Field(default=0, ge=-100, le=100)
    willpower: int = Field(default=0, ge=-100, le=100)
    independent_submissive: int = Field(default=0, ge=-100, le=100)
    education_level: int = Field(default=0, ge=-100, le=100)
    intimacy: int = Field(default=0, ge=-100, le=100)
    curiosity: int = Field(default=0, ge=-100, le=100)
    humor: int = Field(default=0, ge=-100, le=100)
    aggression: int = Field(default=0, ge=-100, le=100)
    social_energy: int = Field(default=0, ge=-100, le=100)
    adventurousness: int = Field(default=0, ge=-100, le=100)

def _validate_profile(profile_dict: dict) -> BridgeProfile:
    try:
        return BridgeProfile(**profile_dict)
    except Exception as e:
        raise ValueError(f"C# 传入的角色属性字典校验失败: {str(e)}")
```

**禁止**在 `chat()` / `chat_stream()` 中使用 `profile_dict.get('key')` 裸取值。强制先解包为 `BridgeProfile`。

#### 第二道：GIL 安全的流式队列 + 熔断机制
```python
import queue, threading, asyncio, json

def chat_stream(session_id: str, message: str, profile_dict: dict, background: str = ""):
    profile = _validate_profile(profile_dict)

    q = queue.Queue(maxsize=100)  # 防止 OOM
    stop_event = threading.Event()

    def _run_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            async def _stream():
                try:
                    ctx = _prompt_builder.build_full(session_id, message, profile, background)
                    async for chunk in _llm_caller.stream(ctx["messages"]):
                        if stop_event.is_set():
                            break
                        q.put(chunk, timeout=2.0)
                except Exception as e:
                    error_payload = json.dumps(
                        {"_error": True, "message": f"Python后台流处理崩溃: {str(e)}"},
                        ensure_ascii=False
                    )
                    q.put(f"data: {error_payload}\n\n")
                finally:
                    q.put(None)

            loop.run_until_complete(_stream())
        finally:
            loop.close()

    t = threading.Thread(target=_run_loop, daemon=True)
    t.start()

    try:
        while True:
            try:
                token = q.get(timeout=1.0)
            except queue.Empty:
                if stop_event.is_set():
                    break
                continue
            if token is None:
                break
            yield token
    finally:
        stop_event.set()
        t.join(timeout=2.0)
```

#### 第三道：异常透传到 C# 侧
```python
def chat(session_id: str, message: str, profile_dict: dict, background: str = "") -> dict:
    try:
        profile = _validate_profile(profile_dict)
        # ... 完整调用链路 ...
        return result
    except Exception as e:
        return {"_error": True, "message": str(e)}
```

##### Scenario: C# 传入非法 profile
- **WHEN** C# 传 `profile_dict = {"rational_emotional": 999}`（超界）
- **THEN** `_validate_profile()` 抛 `ValidationError` → `chat()` 返回 `{"_error": True, "message": "..."}` → C# `PythonBridge` 捕获后弹出错误提示

##### Scenario: 流式线程残留清理
- **WHEN** C# 前端关闭窗口 → `stop_event.set()` + `q.get(timeout=1.0)` 超时感知 → `t.join(timeout=2.0)` 强制回收守护线程

### Requirement: 会话 LiteDB 持久化（体验闭环）
The system SHALL 将所有会话数据持久化到 LiteDB 单文件数据库 `%APPDATA%/MISS/miss.db`，确保重启后对话历史不丢失。

#### 持久化时机与策略
| 触发事件 | 保存时机 | 策略 |
|----------|---------|------|
| 发送消息 | 消息追加到 `_allMessages` 后 | 后台线程防抖保存（300ms 合并窗口） |
| 新建会话 | Session 追加到 `Sessions` 后 | 立即保存 |
| 切换会话 | `CurrentSession` 变更时 | 立即保存 |
| 删除会话 | Session 移除后 | 立即保存 |

#### 防抖实现（C# 侧）
```csharp
private CancellationTokenSource? _saveDebounceToken;

private async void DebouncedSaveSessions()
{
    _saveDebounceToken?.Cancel();
    _saveDebounceToken = new CancellationTokenSource();
    try
    {
        await Task.Delay(300, _saveDebounceToken.Token);
        LocalStore.SaveSessions(Sessions.ToList());
    }
    catch (TaskCanceledException) { }
}
```

#### Scenario: 重启恢复
- **WHEN** 用户关闭程序后重新双击 `MISS.exe`
- **THEN** 侧边栏加载之前所有的会话和角色数据，选择上次关闭时的当前会话，对话区恢复消息历史

---

### Requirement: 侧边栏折叠/展开
The system SHALL 在侧边栏头部提供折叠/展开按钮，点击后侧边栏收缩为竖排标签模式。

#### Scenario: 折叠 / 展开
- **WHEN** 用户点击 « / » 按钮
- **THEN** 侧边栏宽度 200px ↔ 38px 切换

### Requirement: ⑨模式主题联动
The system SHALL 通过 `MainViewModel.IsCirnoMode` 驱动全局 DynamicResource 主题切换。

#### ⑨模式色板
| 映射变量 | 正常值 | ⑨模式值 |
|---------|--------|---------|
| PrimaryBrush | #D4786E | #00BFFF |
| PrimaryLightBrush | #FBE5E0 | #D0F0FF |
| BgBrush | #FDF8F0 | #F0F8FF |
| SurfaceBrush | #FFFBFA | #F5FAFE |
| SurfaceAltBrush | #F5EDE3 | #E8F4FC |
| BorderBrush | #E8DDD4 | #B8E0F0 |
| TextBrush | #4A3728 | #2A4A5A |
| TextSecondaryBrush | #8B7355 | #5A8A9A |
| UserBubbleBrush | #F0E6DA | #E8F4FC |
| MissBubbleBrush | #FBE5E0 | #E0F0FA |

#### Scenario: 触发 / 退出⑨模式
- **WHEN** `education_level == -100` 或选择"笨蛋⑨"角色 → 冰蓝主题 + 徽章显示
- **WHEN** `education_level > -100` 或选择其他角色 → 暖色恢复 + 徽章消失

#### 渲染死角审计（强制）
所有新增控件的颜色必须使用 `DynamicResource`，禁止 `StaticResource` 或硬编码。重点审计区域：会话列表/角色列表 ItemTemplate、消息气泡 DataTemplate、动态生成控件。

### Requirement: 内心独白全局开关
The system SHALL 通过 `MainViewModel.IsInnerThoughtVisible` 绑定到每个 `ChatMessage.IsInnerVisible`，驱动所有气泡内 inner_thought 的显示/隐藏。

#### 滚动平滑处理
批量操作标志 + `Dispatcher.BeginInvoke` 手动 `ScrollToEnd()`，防止 WPF `VirtualizingStackPanel` 高度突变导致滚动条跳动。

### Requirement: 属性面板折叠修复
将折叠手柄从 `AttributePanel` 内部移至 `MainWindow` 层级，确保折叠后按钮仍可点击。

---

## 架构演进：Code-Behind → MVVM

### 旧架构（当前代码）
```
MainWindow.xaml.cs
  ├── 直接持有 _backend, _api (Services)
  ├── 直接持有 RoleSidebar, ConversationView, AttributePanel 引用
  └── 事件转发：RoleSelected → ConversationView.ApplyRole()
```

### 新架构（MVVM）
```
MainViewModel (INotifyPropertyChanged)
  ├── Sessions: ObservableCollection<SessionData>     → ListBox.ItemsSource {Binding Sessions}
  ├── Roles: ObservableCollection<RoleData>           → ListBox.ItemsSource {Binding Roles}
  ├── CurrentSession: SessionData?                     → 会话选中态 + 对话区标题
  ├── CurrentRole: RoleData?                           → CollectionViewSource.Filter
  ├── IsInnerThoughtVisible: bool                      → ChatMessage.IsInnerVisible
  ├── IsCirnoMode: bool                                → App.SetTheme()
  └── IsPanelCollapsed: bool                           → AttributePanel.Visibility

ConversationView.xaml.cs
  └── 持有 ViewModel 引用 → SendMessage() 调 ViewModel 方法
```

状态流转路径：
```
User Click → XAML Binding → ViewModel Property Setter → INotifyPropertyChanged → UI Refresh
```
不再出现 `code-behind` 中 `foreach (var msg in _messages)` 的写法。
