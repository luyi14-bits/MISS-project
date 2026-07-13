# MISS 小姐

> **我们不对用户的偏好做任何假设。**
>
> MISS 不是预制角色的集合——她是零基线的空白画布。你的每一次滑动条调节，不是在微调一个已有的 AI 女友模板，而是在从零开始定义"她"是谁。

**MISS**（**M**alleable **I**ntelligent **S**ynthetic **S**oul）是一个以双轨思维引擎驱动的 AI 角色对话框架。支持 10 维动态属性调节、ST 角色卡导入/导出、知识天花板约束和⑨模式彩蛋。新增 AI 角色工厂、知识领域约束、TTS 语音合成、Whisper 离线语音输入、多人角色房间。全栈 Python + Jinja2 + FastAPI，桌面版 WPF（C#/.NET）+ pythonnet 单进程嵌入。AGPL v3 开源。

pytest **~190/190** · xUnit **9/9** · Spec **15/15 PASS** · 安全 **A（51/51）** ✅

---

## 📑 目录

- [她和其他 AI 伴侣有什么不同？](#她和其他-ai-伴侣有什么不同)
- [核心架构](#核心架构)
- [10 维属性面板](#10-维属性面板)
- [🤖 AI 角色工厂（Phase 5 新增）](#ai-角色工厂phase-5-新增)
- [🔊 TTS 语音合成（Phase 6 新增）](#tts-语音合成phase-6-新增)
- [角色头像库](#角色头像库)
- [彩蛋：⑨模式](#彩蛋模式)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [状态声明](#状态声明)
- [路线图](#路线图)
- [参与贡献](#参与贡献)
- [许可证](#许可证)
- [FAQ](#faq)

---

## 她和其他 AI 伴侣有什么不同？

市面上的 AI 伴侣产品（星野、猫箱、筑梦岛、Character.AI）有一个共同的底层假设：**"我们帮你预设好了角色，你选一个就行。"** 它们提供预制模板——傲娇、温柔、高冷——用户在模板上微调，本质上是"选择"而非"创造"。

MISS 拒绝这个假设。

| | 传统 AI 伴侣 | MISS 小姐 |
|---|---|---|
| **角色起点** | 预制模板（傲娇/温柔/高冷...） | 零基线。10 个维度全部从 0 开始，双向可调 |
| **内心活动** | 无。角色"想什么"和"说什么"是同一套逻辑 | 双轨引擎。Track A 真实想法 ≠ Track B 说出口的话 |
| **知识边界** | 无论人设，底层全知模型照常回答一切 | 知识天花板。笨蛋美人真的不懂 GIL，不是装的 |
| **性格深度** | 语气标签叠加 | 10 维属性 + 交叉影响矩阵。高独立+高亲密 = 傲娇式推拉，不是"贴了傲娇标签所以傲娇" |
| **彩蛋** | 无 | 文化水平拉到 -100 触发⑨模式——名字变 MISS⑨，口癖 BAKA~ |
| **客户端** | 纯 Web | Web + WPF 桌面版（pythonnet 同进程嵌入，零端口占用） |

---

## 核心架构

```
用户输入
    │
    ▼
┌─────────────────────────────────────┐
│           Prompt Builder             │
│  (Jinja2 动态渲染系统提示词)          │
└─────────────────────────────────────┘
    │
    ▼
┌──────────────┐   ┌──────────────┐
│  Track A     │   │  Track B     │
│  情感直觉轨   │   │  逻辑推理轨   │
│              │   │              │
│  直觉、感性   │   │  理性、过滤   │
│  快速反应     │   │  社会化审查   │
└──────┬───────┘   └──────┬───────┘
       │                  │
       └──────┬───────────┘
              ▼
     ┌────────────────┐
     │   融合仲裁层     │  ← 好感度 + 人格属性过
     │   Arbitrator   │    滤 Track A 的真实想法
     └───────┬────────┘
             ▼
     ┌────────────────┐
     │   知识天花板     │  ← 学历、专业领域、语言
     │ Knowledge      │    能力、推理深度四维截断
     │   Ceiling      │
     └───────┬────────┘
             ▼
     ┌────────────────┐
     │   JSON 输出     │
     │ {inner_thought, │
     │  spoken}        │
     └────────────────┘
```

**Track A（情感直觉轨）**：角色的真实想法。用户不可见。产生最原始的情感反应。

**Track B（逻辑推理轨）**：社会化表达。用户可见。根据好感度、人格属性对 Track A 的内容进行过滤、扭曲或压抑后输出。

**知识天花板（Knowledge Ceiling）**：四维约束——学历等级、专业领域、语言能力、推理深度——确保一个设定为"小学生"的角色不会回答出大学水平的专业问题。

---

## 10 维属性面板

所有维度默认从 **0（中性）** 开始，范围 -100 ~ +100（亲密度除外）：

| 属性 | -100 端 | +100 端 | 特殊机制 |
|---|---|---|---|
| **理智—情绪** | 纯理性机器，共情归零 | 纯情绪驱动，凭直觉行事 | 两端都无法进行正常恋爱互动 |
| **意志力** | 毫无主见，极易被 PUA | 钢铁意志，死不认错 | 过低时理智属性被部分覆盖 |
| **独立—顺从** | 拒绝一切帮助 | 所有决定需用户拍板 | 与亲密度交叉产生傲娇/粘人 |
| **文化水平** | ⑨级笨蛋，仅理解最基础日常用语 | 博学通才，跨领域知识储备 | **拉到 -100 触发⑨彩蛋** |
| **亲密度** | 0（陌生人）| 100（灵魂伴侣） | 全属性"情绪放大器" |
| **好奇心** | 对世界毫无兴趣 | 无止境追问"为什么" | 与低文化组合→好奇笨蛋 |
| **幽默感** | 严肃到窒息 | 没正经，凡事都要抖包袱 | 与攻击性交叉→毒舌/自嘲 |
| **攻击性** | 绝对和平主义 | 火药桶，一言不合开怼 | 与高意志组合→战姬型 |
| **社交能量** | 深度社恐，三句想逃 | 社交永动机 | 与独立度交叉产生孤高/纠结 |
| **冒险精神** | 安全至上主义 | 极限追逐者 | 与低意志组合→危险莽撞 |

### 属性交叉影响

| 组合 | 效果 |
|---|---|
| 文化 -100 + 好奇 +100 | **好奇笨蛋**：十万个为什么但每个答案都听不懂 |
| 独立 -100 + 亲密 +100 | **傲娇恋人**："我喜欢你但我不能依赖你" |
| 独立 +100 + 亲密 +100 | **粘人精**：用户是她世界的全部重心 |
| 攻击 +100 + 幽默 +100 | **毒舌喜剧人**：每句话都气人但每句话都好笑 |
| 意志 -100 + 亲密 +100 | **玻璃心恋人**：一句话让她自我怀疑一整天 |

---

## 🤖 AI 角色工厂（Phase 5 新增）

**一键生成完整角色，无需手动填入属性。**

输入一句种子描述（如"一个喜欢在深夜弹钢琴的独居钢琴家"），`RoleFactory` 通过**一次 instructor LLM 调用**生成完整角色：

- ✅ 角色名、描述、背景故事
- ✅ 10 维属性数值（自动匹配人设）
- ✅ 领域标签（科学/人文/艺术/技术）
- ✅ 推荐头像风格描述
- ✅ 语音预设（VoicePreset）

不再需要 `analyze_character()` 做第二次 LLM 调用——`GeneratedRole` 内嵌 `AnalysisResult`，一次 API 费用搞定。

### 知识领域约束引擎（KnowledgeDomain）

角色创建时选择的领域标签会注入系统提示词，**前置约束** LLM 的知识范围：

```
角色标签：[科学, 技术]
→ LLM 收到指令："你只了解科学和技术领域的内容"
→ 用户问"唐朝皇帝是谁" → LLM 回答"我不太了解历史"（非装傻，是提示词层约束）
```

优化：当 `allowed_domains` 存在时，`KnowledgeFilter.filter_response()` 降级为仅日志（不执行后处理装傻），避免"双重装傻"。

---

## 🔊 TTS 语音合成（Phase 6 新增）

每个 MISS 角色都有声音了。消息气泡旁新增 🔊 播放按钮，使用 **Edge TTS（微软免费 TTS 服务）** 合成语音：

- **5 种音色自动映射**：根据角色属性（高攻击→语速快、高社交→活泼、低文化→语速慢）
- **NAudio 纯托管播放**：不引入外部依赖，进程内直接播放
- **降级方案**：Edge TTS 不可用时自动降级到 Windows SAPI5（`pyttsx3`）完全离线

```
ConversationView 消息气泡
  └── 🔊 按钮 Click
       └── PythonBridge.TtsSpeak(text, voice)
             └── EdgeTTSEngine → MP3 bytes
                   └── AudioPlayer.PlayAsync(bytes)
```

> ⚠️ Edge TTS 依赖微软非官方 WebSocket 端点，未来可能需要迁移。当前含降级方案保底。

---

## 角色头像库

`avatars/` 目录包含 14 个角色头像，其中 4 个内置预设 + 8 个可选用角色：

| 预设 | 头像 | 人设 |
|------|------|------|
| 傲娇女友 | `p-tsundere.jpg` | 金发双马尾，脸红别扭 |
| 知性姐姐 | `p-intellectual.jpg` | 深棕波浪发+眼镜，温柔知性 |
| 笨蛋⑨ | `p-baka.jpg` | 冰蓝短发冰妖精，天真烂漫 |
| 冰山美人 | `p-icequeen.jpg` | 银白长发，冷艳疏离 |

另有 8 个扩展角色（病娇、女王、小恶魔、天然呆、元气少女、三无、中二病、邻家女孩）可选配。详见 [`avatars/README.md`](./avatars/README.md)。

---

## 彩蛋：⑨模式

当 **文化水平** 被手动拉到 **-100** 时触发：

- 角色名自动变为 **MISS⑨**（蓝色高亮 `#00BFFF`）
- 口癖注入 **"BAKA~"**，每 3-5 句自然使用一次
- 头像增加蓝色冰晶标识
- 约 30% 概率给出天真但完全错误的答案
- 滑块移出 -100 立即解除

---

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/your-org/miss.git
cd miss/miss-backend

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置
cp .env.example .env
# 编辑 .env，填入你的 OPENAI_API_KEY 或其他兼容 API 地址

# 4. 启动 Web 版
python -m uvicorn main:app --host 127.0.0.1 --port 8000

# 5. 浏览器打开
# http://127.0.0.1:8000/demo
```

### 桌面版

WPF 桌面版（`miss-desktop-wpf/`）通过 pythonnet 同进程嵌入 Python 运行时，零端口占用。启动方式：

```powershell
# 1. 安装嵌入版 Python 3.12 + 依赖
cd miss-desktop-wpf\build
.\build.ps1

# 2. 编译运行（需 .NET 8 SDK）
dotnet run
```

详见 [`miss-desktop-wpf/`](./miss-desktop-wpf/) 目录。

---

## 项目结构

```
MISS/
├── README.md                         # 项目总览（本文件）
├── CLA.md                           # 贡献者许可协议
├── CONTRIBUTING.md                  # 贡献指南
├── CODE_OF_CONDUCT.md               # 行为准则
├── CHANGELOG.md                     # 版本发布历史
├── SECURITY.md                      # 安全策略披露
├── LICENSE                           # GNU AGPL v3
├── .gitignore                        # Git 忽略规则
│
├── .github/                            # GitHub 社区规范
│   ├── CODEOWNERS
│   ├── ISSUE_TEMPLATE/  (bug + feature)
│   └── PULL_REQUEST_TEMPLATE.md
│
├── avatars/                          # 角色头像库（14 个角色 + 说明文档）
│   ├── README.md                     #   头像命名规范与角色人设
│   ├── m-miss-default.jpg            #   MISS 默认头像
│   ├── m-user-avatar.jpg             #   用户默认头像
│   ├── p-tsundere.jpg                #   傲娇女友
│   ├── p-intellectual.jpg            #   知性姐姐
│   ├── p-baka.jpg                    #   笨蛋⑨
│   ├── p-icequeen.jpg                #   冰山美人
│   └── p-*.jpg                       #   8 个扩展角色
│
├── docs/                             # 项目文档（6 份技术文档 + release notes + SOP）
│   ├── 技术白皮书.md                   #   C#/Python 全栈架构
│   ├── 安全技术文档.md                 #   安全等级 A · 38 项修复 · 5 阶段审计
│   ├── 验收测试技术文档.md              #   63 问题追踪 · 190 pytest · 双轨测试
│   ├── 安全开发规范_审计报告与修复方案.md
│   └── release-v0.4.0.md              #   Alpha v0.4 发布说明
│
├── 验收报告/                          # 各阶段验收报告（18 份，63 个问题全部追踪）
│   ├── Task_1.1_验收报告.md           #   MISSProfile 属性模型
│   ├── Task_1.2_验收报告.md           #   ⑨模式彩蛋
│   ├── Task_1.3_验收报告.md           #   交叉影响矩阵
│   ├── ...                            #   共 18 份报告
│   ├── 问题反馈汇总.md                #   63 个问题全量追踪
│   └── 项目终验报告.md                #   终验 PASS，pytest ~190
│
├── .design_assets/                    # 设计素材（原型头像、风格对比）
│
├── miss-backend/                      # 后端服务（FastAPI + SQLAlchemy + ChromaDB）
│   ├── main.py                        #   FastAPI 入口 + lifespan
│   ├── config.py                      #   Pydantic Settings 配置
│   ├── database.py                    #   SQLAlchemy 引擎
│   ├── limiter.py                     #   slowapi 速率限制
│   ├── requirements.txt               #   Python 依赖
│   ├── .env.example                   #   环境变量模板
│   ├── models/                        #   数据模型（4 个表）
│   │   ├── session.py
│   │   ├── message.py
│   │   ├── memory.py
│   │   └── preset.py
│   ├── services/                      #   业务服务（12 个模块）
│   │   ├── attribute_engine.py        #     MISSProfile + EasterEgg + CrossEffect + PromptMapper + KnowledgeFilter
│   │   ├── prompt_builder.py          #     4 步流水线组装 LLM messages
│   │   ├── llm_caller.py              #     OpenAI API 调用 + 三级 fallback + 流式 SSE
│   │   ├── memory_manager.py          #     ConversationStore（消息持久化 + 滑动窗口）
│   │   ├── memory_scorer.py           #     四维关键词记忆评分引擎
│   │   ├── memory_summarizer.py        #     三级分级存储（保留/摘要/丢弃）
│   │   ├── vector_store.py            #     ChromaDB 向量化 + 语义检索
│   │   ├── crypto.py                  #     Fernet 对称加密
│   │   ├── desktop_bridge.py          #     pythonnet 桥接层（WPF 桌面版调用）
│   │   ├── role_factory.py            #     AI 一键角色生成（Phase 5 新增）
│   │   ├── knowledge_domain.py        #     知识领域约束引擎（Phase 5 新增）
│   │   └── tts_engine.py              #     Edge TTS 语音合成（Phase 6 新增）
│   ├── routers/                       #   API 路由（6 个端点模块）
│   │   ├── chat.py                    #     POST /api/chat + /api/chat/stream
│   │   ├── preset.py                  #     CRUD /api/preset/*
│   │   ├── character.py               #     角色分析 API
│   │   ├── settings.py                #     设置读写 API
│   │   └── admin.py                   #     管理统计 API
│   ├── middleware/                    #   中间件
│   │   └── auth.py                    #     Bearer Token 鉴权
│   ├── templates/
│   │   └── miss_system.j2             #     Jinja2 系统提示词模板（8 个 XML 区块）
│   ├── frontend/                      #   Web 版前端（属性面板 + 聊天 UI + 流式打字）
│   │   ├── index.html
│   │   └── assets/
│   ├── frontend-desktop/              #   桌面版前端
│   │   ├── index.html
│   │   ├── app.js
│   │   ├── store.js
│   │   └── style.css
│   ├── docs/                          #   后端技术文档（架构 / Bug 修复 / 功能记录）
│   └── tests/                         #   测试套件
│       ├── conftest.py                #     fixture 层（session/function scope）
│       ├── test_profile.py            #     Pydantic 边界验证
│       ├── test_easter_egg.py         #     ⑨模式触发/解除
│       ├── test_cross_effects.py      #     10 组交叉影响匹配
│       ├── test_prompt_mapper.py      #     属性→XML 片段映射
│       ├── test_template.py           #     Jinja2 模板渲染
│       ├── test_llm_json_parse.py     #     JSON 四级容错
│       ├── test_prompt_builder.py     #     PromptBuilder 端到端
│       ├── test_chat_api.py           #     /api/chat 集成测试
│       ├── test_preset.py             #     预设 CRUD 测试
│       ├── test_memory_scorer.py      #     记忆评分测试
│       ├── test_reasoning_models.py   #     推理模型兼容性测试
│       └── acceptance_*.py            #     各阶段验收脚本
│
├── miss-desktop-wpf/                  # WPF 桌面版（C# + pythonnet × MVVM）
│   ├── App.xaml / App.xaml.cs         #   应用入口（PythonEngine 初始化）
│   ├── MainWindow.xaml / .xaml.cs     #   主窗口
│   ├── ViewModels/
│   │   └── MainViewModel.cs           #   MVVM 核心状态（CommunityToolkit.Mvvm）
│   ├── Views/                         #   XAML 视图（8 个页面/控件）
│   ├── Services/                      #   C# 服务层（8 个服务 + 5 项功能）
│   ├── PythonBridge.cs             #     pythonnet 桥接
│   ├── AudioRecorder.cs            #     🆕 NAudio Push-to-Talk 录音
│   ├── WhisperSttService.cs        #     🆕 Whisper 离线语音转写
│   ├── TavernCardParser.cs         #     🆕 ST V3 PNG 解析器
│   ├── TavernCardExporter.cs       #     🆕 ST V3 PNG 导出器
│   ├── ConversationExporter.cs     #     🆕 对话导出（JSON/HTML/MD）
│   ├── AudioPlayer.cs              #     MP3 播放
│   └── LiteDbLocalStore.cs         #     加密持久化
│   ├── Models/                        #   C# 数据模型（API 响应、角色、会话）
│   ├── Controls/                      #   自定义控件
│   ├── Resources/                     #   样式 + 头像素材
│   ├── build/                         #   打包脚本 + 嵌入版 Python + 依赖清单
│   └── publish/                       #   发布产物
│
├── miss-desktop-pywv（已弃用）/         # 已弃用（PyWebView 方案，保留历史参考）
│
├── miss-market-research/              # 市场调研报告（不上传 Git）
│
├── miss-pipeline/                     # 产品管线看板（HTML Kanban + ECharts）
│   └── miss-pipeline.html
│
├── build/                             # PyInstaller 打包 miss-server.exe
├── dist/                              # 打包分发包
│   └── .trae/                             # 项目工具链（不上传 Git）
    ├── specs/                         #   Spec 任务卡（10 个功能模块）
    │   ├── fix-role-save-and-ui/       #     角色创建 + UI 修复 ✅
    │   ├── desktop-packaging/          #     Tauri 桌面版 ❌ 废弃
    │   ├── desktop-rebuild/            #     WPF MVVM 重构 ✅
    │   ├── desktop-polish/             #     桌面版细节打磨 ✅
    │   ├── fix-binding-and-api/        #     绑定 + API 修复 ✅
    │   ├── fix-llm-api-compat/         #     LLM API 兼容性修复 ✅
    │   ├── fix-license-headers/        #     全项目版权头补全 ✅
    │   ├── fix-residual-risks/         #     加密/SSRF 残余风险修复 ✅
    │   ├── phase5-role-factory-tts/    #     AI 角色工厂 + TTS 语音 ✅
    │   └── fix-role-message-isolation/ #     角色消息隔离修复 ✅（Loop #1 已交付）
    └── skills/                        #   项目 Skill 库（8 个团队角色规范 v3）
        ├── pm-mentor/                  #     产品经理（PRD/优先级/路线图）🆕
        ├── acceptance-testing/         #     验收报告标准（v3：验收人准则+陷阱清单）
        ├── coding-ethics/              #     编程八荣八耻（v3：XAML/线程安全/LiteDB）
        ├── project-secretary/          #     项目秘书（文件整理/管线维护/标准审计）
        ├── security-academy/           #     安全专家组（v3：STRIDE+5层防御+审计流程）
        ├── spec-pipeline/              #     管线工程师（v2：优先级矩阵+置信度审计）
        ├── test-driven-development/    #     测试方法论（TDD + pytest + E2E）
        └── trinity-mentors/            #     AI/ML 导师团
```

> **注**：Track A（内心独白）和 Track B（说出口的回应）在提示词层实现（参见 `miss_system.j2` 的 `<cognitive_engine>` 块），不是独立的 Python 模块。知识天花板约束在 `miss_system.j2` 中注入提示词层，并在 `KnowledgeFilter` 中做后端二次校验。架构细节见 [`miss-backend/docs/architecture.md`](./miss-backend/docs/architecture.md)。

---

## 状态声明

```
█████████████████████████████████████████████
█                                           █
█   BETA v0.7 — 安全等级 A                     █
█                                           █
█   多人角色房间 · DeepSeek 兼容 · 安全 51/51 ✅  █
█   Spec 15/15 PASS · xUnit 9/9 · pytest 190  █
█   标准文件 8/8 · 想法池 3 项。                █
█   欢迎 Star / Watch 以跟踪进展。             █
█                                           █
█████████████████████████████████████████████
```

---

## 路线图

| 阶段 | 内容 | 状态 |
|------|------|------|
| **Phase 0-4** | 核心引擎 + API + 记忆系统 | ✅ PASS |
| **Phase 7** | 单元测试 + 集成测试 | ✅ PASS |
| **fix-role-save-and-ui** | 角色创建保存 + 全界面"角色"命名统一 | ✅ PASS |
| **desktop-packaging** | Tauri 桌面版 v2 | ❌ 废弃 |
| **desktop-rebuild** | WPF MVVM 重构（pythonnet 单进程） | ✅ PASS |
| **desktop-polish** | 全线 21 项修复（启动线程/主题/IO/日志） | ✅ PASS |
| **fix-binding-and-api** | 推理模型兼容 + 属性面板/标题栏/设置持久化 | ✅ PASS |
| **fix-llm-api-compat** | 三级 API fallback（TOOLS→JSON→Raw） | ✅ PASS |
| **fix-license-headers** | 全项目 SPDX 版权头补全（78 源文件） | ✅ PASS |
| **fix-residual-risks** | 记忆加密对齐 + Fernet 持久化 + SSRF 防护 | ✅ PASS |
| **安全审计 5 阶段** | 认证·加密·限流·去匿名化·打包（38/38） | ✅ PASS |
| **Phase 5（新增）** | AI 角色工厂 + 知识领域约束引擎（精简方案：40→18 任务） | ✅ PASS |
| **Phase 6（新增）** | TTS 语音合成（edge-tts + NAudio）、AudioPlayer | ✅ PASS |
| **fix-role-message-isolation** | 角色切换消息隔离（Loop #1 已交付） | ✅ PASS |
| **对话导出** | JSON/HTML/Markdown 三格式，对话栏 📥 按钮 | ✅ PASS |
| **sillytavern-card-compat** | SillyTavern V3 角色卡 PNG 导入/导出 (5 Tasks) | ✅ PASS |
| **xUnit 测试** | C# 单元测试基础设施，CoreDomainTests 9/9 PASS | ✅ PASS |
| **语音输入 STT** | Whisper.net ggml-tiny 离线转写，🎤 Push-to-Talk | ✅ PASS |
| **多人角色房间** | 后端 API + C# 桥接 + UI（广播模型 + 上下文感知） | ✅ PASS |
| **DeepSeek 兼容修复** | 流式沉默失败 5 项修复 + 非流式 instructor 跳过 | ✅ PASS |
| **安全增量审计** | N01-N13 修复（sessionStorage / PDB / DB 清理 / Schema 校验） | ✅ PASS |
| **v1.0** | 全功能 MCP Server + 社区预设市场 + 完整测试覆盖 | 💡 想法池 |

---

## 参与贡献

MISS 是一个个人练手项目。欢迎任何形式的讨论、反馈和代码审查。

1. Star 本仓库跟踪进展
2. 阅读 [`miss-backend/docs/architecture.md`](./miss-backend/docs/architecture.md) 了解完整架构设计
3. 在 Discussions 中分享你对 AI 陪伴产品设计的想法

PR 欢迎提交。任何贡献——哪怕是一个 typo 修复——都会在 README 的致谢区署名。

---

## 许可证

GNU Affero General Public License v3.0

参见 [LICENSE](./LICENSE)

核心原则：
- 你可以在任何地方使用、修改和分发这个项目
- 如果你基于此项目构建了衍生产品并对外提供服务，你必须开源你的修改
- 大厂不会碰 AGPL 项目。这意味着你的贡献不会被一家公司锁死

---

## FAQ

**Q: 为什么全开源？不怕竞品抄袭？**

A: 双轨引擎、知识天花板、MISS 零基线的精髓在产品和架构设计，不在代码行数。一个有能力的工程师看懂了 README 和架构图就能理解我们在做什么——他看了代码只会更认可。竞品（星野/猫箱/筑梦岛）的壁垒在模型、流量和 IP，不在"有没有人开源了一个角色引擎"。真正可能抄袭你的独立开发者——在 AGPL 下他的项目也必须开源，等于免费帮你传播。

**Q: 需要自己带 API Key 吗？**

A: 是。在 `.env` 中填入 `OPENAI_API_KEY`（或其他兼容 API 的 base_url + key）。

**Q: 你的产品哲学和 Character.AI / 星野最核心的差异是什么？**

A: 他们让你**选择**一个 AI 女友模板。我们让你**创造**她。这八个字是 MISS 和整个市场的根本分界线。
