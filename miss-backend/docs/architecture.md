# MISS 技术架构文档

> 版本：Alpha v0.2 · 更新：2026-06-28 · 架构：C# WPF 桌面应用 + 嵌入式 Python

---

## 1. 系统概览

MISS 是一个 **C# WPF (.NET 8) 桌面应用**，内嵌 **Python 3.12** 运行时，通过 **pythonnet** 实现 C# ↔ Python 双向调用。整体为**单进程模型**——无 HTTP 端口、无 Web 服务器、无外部 API 暴露。

```
┌───────────────────────────────────────────────────────────────┐
│                    MISS Desktop (单进程)                       │
│                                                               │
│  ┌──────────────────────┐     pythonnet      ┌─────────────┐  │
│  │    C# WPF 层          │◄──────────────────►│  Python 层   │  │
│  │                       │   Py.GIL() + STA   │              │  │
│  │  App / MainWindow     │   BlockingCollection│  services/  │  │
│  │  MainViewModel (MVVM) │                    │  desktop_   │  │
│  │  PythonBridge         │                    │  bridge.py  │  │
│  │  LiteDbLocalStore     │                    │  llm_caller │  │
│  └───────────────────────┘                    └──────────────┘  │
│                                                               │
│  持久化: LiteDB (miss.db)   数据库: SQLite (WAL mode)          │
│  向量库: ChromaDB (PersistentClient)                          │
└───────────────────────────────────────────────────────────────┘
```

**关键设计决策：**

| 决策 | 说明 |
|------|------|
| C# WPF + 嵌入式 Python | 利用 WPF 原生桌面体验，Python 承载 AI/记忆/属性引擎 |
| pythonnet 桥接 | 单 STA 线程 + `Py.GIL()` + `BlockingCollection<Action>` 序列化所有 Python 调用 |
| 无 HTTP 层 | 桌面应用直接调用 Python，无端口占用、无网络攻击面 |
| LiteDB 本地加密存储 | 消息文本/InnerThought 经 Fernet 加密后写入 BSON，API Key 同理 |

---

## 2. 一次完整对话的数据流

```
用户输入 "今天的你特别可爱。" → 回车
    │
    ├─ ConversationView 绑定 → MainViewModel.SendMessageCommand
    │
    ├─ C# PythonBridge.Chat(sessionId, message, profile)
    │     └─ RunOnPythonThread(() => { ... })
    │         ├─ BlockingCollection<Action> 排队到 STA 线程
    │         ├─ using (Py.GIL()) 获取 GIL
    │         └─ services.desktop_bridge.chat(session_id, message, profile_dict)
    │
    ├─ [Python] desktop_bridge.chat()
    │     ├─ BridgeProfile.model_validate(profile_dict)  → 严格 ge/le 校验
    │     ├─ PromptBuilder.build_full(session_id, message, profile)
    │     │     ├─ EasterEggEngine.evaluate(profile)
    │     │     ├─ CrossEffectCalculator.calculate(profile)
    │     │     ├─ AttributePromptMapper.map_all(profile)
    │     │     ├─ VectorMemoryStore.recall(message)
    │     │     ├─ Jinja2 渲染 miss_system.j2 → system_prompt
    │     │     └─ ConversationStore.get_window(session_id)
    │     │     → messages = [system, ...window, user]
    │     │
    │     ├─ LLMCaller.call(messages)
    │     │     ├─ 推理模型检测: _is_reasoning_model(model)
    │     │     ├─ Level 1: instructor Mode.TOOLS (或 Mode.JSON for 推理模型)
    │     │     ├─ Level 2 (fallback): 裸 AsyncOpenAI + response_format=json_object
    │     │     └─ Level 3 (fallback): 裸 AsyncOpenAI + system prompt JSON 指令
    │     │     → {"inner_thought":"...", "spoken":"..."}
    │     │
    │     ├─ KnowledgeFilter.filter_response(result, education_level)
    │     └─ 返回 dict → C# 反序列化为 ChatResponse
    │
    ├─ [C#] MainViewModel 接收 ChatResponse
    │     ├─ 创建 ChatMessage (IsUser=false, Text=response.Spoken, InnerThought=...)
    │     ├─ LiteDbLocalStore.SaveMessages(session) → EncryptMessage 加密后存 BSON
    │     └─ ObservableCollection 更新 → UI 绑定的 MessagesView 自动刷新
    │
    └─ 用户看到角色回复，点击 "内心想法" CheckBox → InnerThought 显示
```

---

## 3. C# 模块职责

### 3.1 App.xaml.cs — 应用生命周期

- `OnStartup`: 立即创建 MainWindow（`IsEnabled=false`），`Task.Run` 异步初始化 Python，完成后 `Dispatcher.Invoke` 启用窗口
- `DispatcherUnhandledException` 全局异常处理 → 写入 `crash.log`
- `SetTheme(bool isCirno)`: 根据 ⑨ 模式切换暖色调 / 冰蓝色调，通过 `DynamicResource` 动态替换调色板

### 3.2 MainViewModel.cs — 核心 ViewModel（MVVM）

- **Singleton** 模式，全局唯一实例
- `[ObservableProperty]` 属性: `_sessions`, `_roles`, `_currentSession`, `_currentRole`, `_isInnerThoughtVisible`, `_isCirnoMode`, `_isPanelCollapsed`
- `[RelayCommand]` 命令: `CreateSession`, `DeleteSession`, `ToggleInnerThought`
- `CollectionViewSource` 按角色名过滤消息列表
- `TiktokenTokenizer` 精确 token 计数
- `OnCurrentRoleChanged`: 检测 `EducationLevel == -100` → 触发 `IsCirnoMode`
- `OnIsCirnoModeChanged`: 调用 `App.SetTheme()` 切换主题
- `DebouncedSaveSessions`: 300ms 防抖保存，`CancellationTokenSource` 控制

### 3.3 PythonBridge.cs — C# ↔ Python 桥接器

- **静态类**，所有 Python 调用统一入口
- `RunOnPythonThread`: 专用 STA 线程 + `BlockingCollection<Action>` + `Py.GIL()` 序列化执行
- 代理方法: `Chat`, `ChatStream`, `AnalyzeCharacter`, `ApplySettings`, `GetSettings`
- `EncryptMessage` / `DecryptMessage` 调用 `services.crypto`
- `MarkInitialized` / `MarkDisposed` 守卫防止未初始化调用

### 3.4 PythonEngineService.cs — Python 运行时初始化

- 三级查找: `embedded/python/` → `C:\Program Files\Python312` → `C:\Python312`
- 初始化 `PythonEngine` + 导入 `desktop_bridge` 模块

### 3.5 LiteDbLocalStore.cs — 本地加密持久化

- LiteDB 单文件数据库 → `%APPDATA%/MISS/miss.db`
- `SaveMessages`: `EncryptIfNotEmpty` 加密 Text/InnerThought 后写入 BSON
- `SaveSettings`: API Key 先加密再 JSON 序列化，`finally` 块恢复明文
- `LoadMessages`: 读取时解密
- `DeleteSession`: 完整实现
- 实现 `ILocalStore` 接口（13 个方法）

### 3.6 辅助模块

| 模块 | 职责 |
|------|------|
| `NotificationService` | 静态类，封装 `MessageBox` 的 Info/Confirm/Error |
| `InverseBooleanConverter` | 布尔取反值转换器 |
| `InverseBooleanToVisibilityConverter` | 布尔取反 → Visibility 转换器 |
| `ChatMessage` | `ObservableObject`，含 Text, InnerThought, IsUser, IsInnerVisible, Sender, RoleName, TokenCount |

### 3.7 Views — XAML 界面

| 视图 | 说明 |
|------|------|
| `MainWindow.xaml` | 三列 Grid: RoleSidebar(200px) + ConversationView(*) + AttributePanel(ToggleButton 折叠)。Window.Resources 注册 InvertConverters |
| `ConversationView.xaml` | 标题栏（会话标题 + 当前角色名）、内心想法 CheckBox、MessagesView 绑定 |
| `RoleSidebar.xaml` | 会话区域（含删除按钮）+ 角色区域、折叠按钮 |
| `AttributePanel.xaml` | 10 个硬编码 Slider，每个 `TwoWay` 绑定到 `CurrentRole.Profile.XXX`（无 ItemsControl / SliderItem 类） |
| `SettingsWindow.xaml` | API Key、Base URL、模型等设置 |
| `CreateRoleWindow.xaml` | 新建角色配置 |

### 3.8 数据模型（C# 侧）

| 模型 | 说明 |
|------|------|
| `MISSProfile` | 10 维属性（索引访问 + `Clone` 方法），ge=-100/le=100，intimacy ge=0/le=100 |
| `RoleData` | 角色名称 + MISSProfile |
| `SessionData` | 会话 ID、标题、创建/更新时间、消息列表 |
| `SettingsData` | API Key、Base URL、模型、温度等 |
| `ChatResponse` | InnerThought, Spoken, EasterEggs, CrossEffects |

---

## 4. Python 模块职责

### 4.1 desktop_bridge.py — C# 入口适配层

- 同步函数，供 pythonnet 直接调用
- `BridgeProfile(BaseModel)`: 严格的 `ge`/`le` 字段级验证
- `chat()`: 异常包装为 `{"_error": True, "message": str(exc)}`，确保 C# 侧永远收到合法 dict
- `chat_stream()`: `Queue(maxsize=100)` + `threading.Event` 断路器
- `analyze_character()`: 委托 `LLMCaller.analyze_character()`

### 4.2 llm_caller.py — LLM API 调用器

**三级回退策略** (`call()`):

```
Level 1: instructor Mode.TOOLS（结构化输出，最可靠）
    ├─ 推理模型 → 跳过 TOOLS，降级为 Mode.JSON
    └─ 成功 → 返回 Pydantic 模型

Level 2: 裸 AsyncOpenAI + response_format={"type":"json_object"}
    ├─ chat.completions.create(...)
    ├─ response_format 强制 JSON 输出
    └─ json.loads(content) → dict

Level 3: 裸 AsyncOpenAI + system prompt JSON 指令
    ├─ system prompt 追加 "请返回纯 JSON 格式"
    ├─ json.loads(content) → dict
    └─ json.JSONDecodeError → 返回安全占位符（绝不返回 LLM 原始文本）
```

**推理模型自动检测:**

```python
_REASONING_MODELS = {"reasoner", "o1", "o3", "v4-pro", "v4-flash"}
_is_reasoning_model(model) → 自动跳过 instructor TOOLS 模式
```

**容错保障:**
- 所有 `except` 块均含 `logging.warning`
- `_parse_json_response`: 解析失败时**丢弃原始文本**，返回安全占位符（SEC 注释标注的安全要求）
- `analyze_character()`: 独立三级回退，每级均记录日志
- `stream()`: instructor → 裸 client 回退

### 4.3 attribute_engine.py — 属性引擎

| 类 | 职责 |
|----|------|
| `MISSProfile` | Pydantic BaseModel，10 维双向属性 ±100 + intimacy 0-100，字段级 ge/le 验证 |
| `EasterEggEngine` | education_level=-100 → 触发 ⑨ 模式 |
| `CrossEffectCalculator` | 10 组交叉影响规则精确匹配 → 返回激活的交叉人格 |
| `AttributePromptMapper` | 每个属性 7 级分层 → XML 片段 → `map_all()` 汇总 |
| `KnowledgeFilter` | 低教育水平时检测专业术语 → 替换/降级 |
| `IntimacyEngine` | 亲密度相关逻辑处理 |

### 4.4 prompt_builder.py — 提示词编排器

`build_full()` 按顺序编排:

```
EasterEggEngine.evaluate()
  → CrossEffectCalculator.calculate()
    → AttributePromptMapper.map_all()
      → VectorMemoryStore.recall()   ← 向量语义检索
        → Jinja2 渲染 miss_system.j2 → system prompt
          → ConversationStore.get_window() → 最近对话窗口
```

- 向量检索失败时 `logging.warning`，不中断流程
- 返回 `{messages, active_easter_eggs, active_cross_effects}`

### 4.5 记忆系统（三层架构）

```
┌─────────────────────────────────┐
│  工作窗口 (ConversationStore)    │  ← SQLite messages 表，最近 20 轮
├─────────────────────────────────┤
│  长期记忆 (MemoryEntry)          │  ← SQLite memory_entries 表
├─────────────────────────────────┤
│  语义检索 (VectorMemoryStore)    │  ← ChromaDB PersistentClient
└─────────────────────────────────┘
```

**ConversationStore** (`memory_manager.py`):
- `add_message()` / `get_window()` 含事务保护（`rollback + raise`）
- `get_overflow_messages()`: 检测超出窗口的消息 → 送入压缩管线

**MemoryScorer** (`memory_scorer.py`):
- **纯本地关键词评分**: 长度分(0-30) + 关键词分(0-40) + 角色分(0-15) + 情感密度分(0-15)
- **不依赖任何外部 API**

**MemorySummarizer** (`memory_summarizer.py`):
- importance ≥ 80 → 保留原文
- 40 ≤ importance < 80 → 截取首句摘要
- importance < 40 → 丢弃
- 向量存储失败时 `logging.warning`

**VectorMemoryStore** (`vector_store.py`):
- `store` / `recall` / `recall_with_threshold` / `sync_from_db` / `age`
- 所有 `except` 块含 `logging.warning`

**记忆老化**:
```
超 max_age_days 天的记忆:
  importance < 40 → 从 DB + ChromaDB 双删
  importance ≥ 40 → importance-10，降至 0 后双删
```

### 4.6 crypto.py — 对称加密

- Fernet 对称加密
- `encrypt()` / `decrypt()`
- 窄异常捕获: `binascii.Error`, `ValueError`
- `MISS_FERNET_KEY` 未设置时 `logging.warning`

---

## 5. API 回退策略（详细）

```
                ┌──────────────────────┐
                │   LLMCaller.call()   │
                └──────────┬───────────┘
                           │
                    ┌──────▼──────┐
                    │ 推理模型检测  │
                    └──┬───────┬──┘
              是推理模型│       │普通模型
                       │       │
              ┌────────▼──┐  ┌─▼──────────────┐
              │ Mode.JSON │  │ Mode.TOOLS      │
              │ (instructor)│ │ (instructor)    │
              └──┬──┬─────┘  └─┬──┬────────────┘
                 │  │          │  │
              成功│  │失败    成功│  │失败
                 │  │          │  │
                 │  │    ┌─────▼──▼──────┐
                 │  └────► Level 2       │
                 │        │ response_     │
                 │        │ format=json   │
                 │        │ _object       │
                 │        └──┬──┬─────────┘
                 │           │  │
                 │        成功│  │失败
                 │           │  │
                 │      ┌────▼──▼──────────┐
                 │      │ Level 3          │
                 │      │ system prompt    │
                 │      │ JSON 指令         │
                 │      └──┬──┬────────────┘
                 │         │  │
                 │      成功│  │失败
                 │         │  │
                 └─────────▼──▼─────────────────┐
                            │ 返回安全占位符       │
                            │ (绝不泄露 raw text) │
                            └────────────────────┘
```

**关键安全约束：**
- 任何层级 `json.JSONDecodeError` → **丢弃 LLM 原始文本**，返回 `{"_error": true, "message": "..."}`
- 所有 `except` 块有 `logging.warning`，无一遗漏
- `_error` 格式在 C# 侧统一处理

---

## 6. 安全架构

### 6.1 加密层级

```
用户消息文本 ──► EncryptMessage(Fernet) ──► BSON 存储 (LiteDB)
角色回复文本 ──► EncryptMessage(Fernet) ──► BSON 存储 (LiteDB)
InnerThought ──► EncryptMessage(Fernet) ──► BSON 存储 (LiteDB)
API Key ───────► Fernet 加密 ──► JSON 序列化 ──► LiteDB
```

- Fernet 密钥由 `MISS_FERNET_KEY` 环境变量注入
- 密钥未设置时 `logging.warning` 警告，不静默失败
- API Key 在 `SaveSettings` 中加密写入，`finally` 块恢复明文

### 6.2 崩溃防护

- `App.DispatcherUnhandledException` → 全局异常捕获 → 写入 `crash.log`
- 应用启动先显示禁用窗口 → Python 初始化完成后启用 → 避免未初始化崩溃

### 6.3 LLM 输出净化

| 防护点 | 措施 |
|--------|------|
| `_parse_json_response` | JSON 解析失败 → 丢弃 raw text（SEC 注释标记） |
| `desktop_bridge.chat()` | 异常包装为 `{"_error": True}`，不向上抛出 |
| `llm_caller.call()` 三级 fallback | 最终失败返回安全占位符，不返回 LLM 原始输出 |
| `logging.warning` 全覆盖 | 所有异常路径均有日志，可审计 |

### 6.4 安全评级

**A- 评级**：27/27 修复项完成，覆盖 4 个阶段。核心修复涵盖：加密（Fernet 消息 + API Key）、崩溃日志、LLM 原始文本零泄漏、`_error` 格式一致性、`except:pass` 清零。

---

## 7. 模板架构 (miss_system.j2)

Jinja2 模板渲染为 system prompt，包含 8 大区块：

| 区块 | 内容 | 备注 |
|------|------|------|
| `<system_directive>` | 核心身份声明：有灵魂的个体，非工具 | 动态 persona_name |
| `<persona>` | 角色名 + ⑨ 口癖（若激活） | 动态 persona_name, cirno |
| `<dynamic_state>` | 10 维属性 XML 描述 | 动态 attribute_xml |
| `<knowledge_ceiling>` | 知识天花板 4 级分支 | 动态 education_level, allowed_domains |
| `<easter_egg>` | ⑨ 模式完整配置 | 动态 cirno dict |
| `<cross_persona>` | 激活的交叉人格列表 | 动态 cross_effects list |
| `<cognitive_engine>` | **Track A + Track B 双轨认知引擎** | 纯指令 |
| `<behavioral_constraints>` | 10 条禁止行为 | 动态 persona_name |
| `<recalled_memories>` | 语义检索到的历史记忆 | 动态 memories list |
| `<response_format>` | JSON 输出模板 | 纯指令 |

### 双轨认知引擎 (Track A / Track B)

```
<cognitive_engine>
  Track A (内心独白):  角色真实想法 → inner_thought 字段（不对用户可见）
  Track B (说出口的回应): 过滤后的表达 → spoken 字段（面向用户）
</cognitive_engine>
```

- LLM 输出 `{"inner_thought":"...", "spoken":"..."}` JSON 格式
- Track A 与 Track B 的"反差"是角色魅力的核心来源
- **双轨逻辑放在提示词层而非代码层**：让模型自己模拟两种思维比代码分拆更自然，且修改双轨逻辑只需编辑模板无需改 Python

---

## 8. 配置

### Python 侧 (`config.py`)

`pydantic-settings` BaseSettings，`.env` 文件驱动：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OPENAI_API_KEY` | `""` | API 密钥 |
| `OPENAI_BASE_URL` | `""` | 自定义 API 端点 |
| `DB_URL` | `sqlite:///./miss.db` | SQLite 路径 |
| `VECTOR_DB_PATH` | `./vector_db` | ChromaDB 持久化路径 |
| `model` | `gpt-4o` | 模型名称 |
| `temperature` | `1.0` | 生成温度 |
| `top_p` | `0.92` | nucleus sampling |
| `max_tokens` | `1024` | 最大输出 token |
| `frequency_penalty` | `0.1` | 重复惩罚 |
| `conversation_window_size` | `20` | 对话窗口大小 |

运行时可通过 `apply_runtime_settings()` 动态覆盖 `openai_api_key`、`openai_base_url`、`model`，使用 `threading.Lock` 保证线程安全。重启后恢复 `.env` 值。

### C# 侧

- `PythonEngineService`: 三级 Python 路径回退
- `%APPDATA%/MISS/miss.db`: LiteDB 数据库路径
- 主题色通过 `DynamicResource` 在暖色/冰蓝两组间切换

---

## 9. 测试

**190 项 pytest 测试**，全部通过。

| 测试文件 | 覆盖模块 |
|----------|----------|
| `test_profile.py` | MISSProfile Pydantic 边界验证 |
| `test_easter_egg.py` | ⑨ 模式触发/解除 |
| `test_cross_effects.py` | 10 组交叉影响 + 边界条件 |
| `test_prompt_mapper.py` | 属性 → XML 映射 |
| `test_template.py` | Jinja2 模板渲染 |
| `test_llm_json_parse.py` | LLM JSON 解析四级容错 |
| `test_prompt_builder.py` | PromptBuilder 端到端编排 |
| `test_chat_api.py` | chat 集成测试 |
| `test_memory_scorer.py` | MemoryScorer + MemorySummarizer |
| `test_preset.py` | 预设 CRUD + 导入导出 |

测试命令: `pytest`

---

## 10. 构建与发布

### 项目结构

```
MISS/
├─ miss-desktop-wpf/        # C# WPF 桌面应用 (.NET 8)
│   ├─ App.xaml.cs          # 应用生命周期 + 主题切换
│   ├─ MainWindow.xaml      # 主界面布局
│   ├─ MainViewModel.cs     # MVVM ViewModel
│   ├─ PythonBridge.cs      # pythonnet 桥接
│   ├─ PythonEngineService.cs # Python 运行时初始化
│   ├─ LiteDbLocalStore.cs  # 本地加密存储
│   ├─ Models/              # C# 数据模型
│   └─ Views/               # XAML 视图
│
├─ miss-backend/            # Python 后端逻辑
│   ├─ services/
│   │   ├─ desktop_bridge.py    # C# 入口适配
│   │   ├─ llm_caller.py        # LLM 调用器 (instructor + 三级回退)
│   │   ├─ attribute_engine.py  # 属性引擎
│   │   ├─ prompt_builder.py    # 提示词编排
│   │   ├─ memory_manager.py    # 对话持久化 (SQLAlchemy + SQLite)
│   │   ├─ memory_scorer.py     # 本地记忆评分
│   │   ├─ memory_summarizer.py # 记忆压缩
│   │   ├─ vector_store.py      # 向量存储 (ChromaDB)
│   │   └─ crypto.py            # Fernet 加密
│   ├─ config.py                # 配置管理
│   ├─ templates/
│   │   └─ miss_system.j2       # 系统提示词模板
│   ├─ tests/                   # pytest 测试 (190 项)
│   └─ docs/
│       └─ architecture.md      # 本文档
│
└─ embedded/
    └─ python/              # 嵌入式 Python 3.12 运行时
```

### 技术栈摘要

| 层级 | 技术 | 用途 |
|------|------|------|
| 桌面框架 | C# WPF (.NET 8) | 用户界面、MVVM |
| Python 集成 | pythonnet 3.x | C# ↔ Python 双向调用 |
| Python 运行时 | Python 3.12 (embedded) | AI 引擎、记忆系统 |
| LLM 结构化输出 | instructor | 一级调用的结构化提取 |
| LLM SDK | AsyncOpenAI (openai 包) | 二/三级回退调用 |
| 消息持久化 | LiteDB | C# 侧加密本地存储 |
| 对话存储 | SQLite + SQLAlchemy | Python 侧 WAL 模式 |
| 向量检索 | ChromaDB (PersistentClient) | 语义记忆 |
| 提示词模板 | Jinja2 | 系统提示词渲染 |
| 加密 | Fernet (cryptography) | 消息 + API Key 对称加密 |
| 测试 | pytest | Python 侧测试 |
