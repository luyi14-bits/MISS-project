# Phase 5+6 — 角色 Factory + 知识域约束 + TTS 语音 Spec

## Why
1. **角色创建依赖用户手动输入**：当前 `analyze_character` 只能从文字描述中提取 10 维属性数值，用户还要手动填角色名、写背景——AI 没有生成"完整角色"的能力
2. **知识域过滤是后处理，不是前置约束**：`KnowledgeFilter.filter_response()` 是在 LLM 已经回复之后才动手脚（碰到复杂词就装傻）——不优雅、且极易被 prompt 注入绕过
3. **无语音能力**：整个项目零 TTS 实现，用户只能看文字——AI 角色没有"声音"

## Meta
- **优先级**: P3（路线图功能，非阻塞发布）
- **Phase 5 估算工时**: 5 人天
- **Phase 6 估算工时**: 4 人天
- **合计**: 9 人天
- **影响 Spec**: 无已有 Spec 受影响（纯新增功能）

## What Changes

### Phase 5: 角色 Factory + 知识域约束
- **新增** `RoleFactory` 类 — LLM 驱动的一键角色生成（名字+描述+背景+10维属性+领域标签+推荐头像）
- **新增** `KnowledgeDomainEngine` — 前置注入领域约束到 system prompt（替代后处理 `KnowledgeFilter.filter_response`）
- **增强** `RoleData.cs` — 新增 `Id`/`Tags`/`VoicePreset`/`CreatedAt` 字段
- **增强** `CreateRoleWindow` — 新增"AI 一键生成"按钮 + 领域选择器

### Phase 6: TTS 语音
- **新增** `tts_engine.py` — Edge TTS 封装（免费、离线、多音色）
- **新增** `POST /api/tts/synthesize` — 文本 → 音频流（WAV/MP3 byte stream）
- **新增** WPF `AudioPlayer` — NAudio 播放组件
- **增强** `RoleData.cs` — 新增 `VoicePreset` 字段
- **增强** `ConversationView` — 消息气泡旁新增 🔊 播放按钮

## Impact
- Affected specs: 无
- Affected code:
  - 新增: `services/role_factory.py`, `services/knowledge_domain.py`, `services/tts_engine.py`
  - 新增: `routers/tts.py`, `Models/RoleData.cs`（增强）, `Services/AudioPlayer.cs`
  - 修改: `CreateRoleWindow.xaml/.cs`, `ConversationView.xaml/.cs`, `prompt_builder.py`, `desktop_bridge.py`

---

## Phase 5 ADDED Requirements

### Requirement: P5-R1 — 角色 Factory 一键生成
The system SHALL 提供 `RoleFactory.generate(seed_text)` → 返回完整 `RoleData`（name + description + background + 10-dim profile + tags + avatar_suggestion）。

```python
# services/role_factory.py
class GeneratedRole(BaseModel):
    name: str = Field(description="角色名字")
    description: str = Field(description="角色特征描述，50-100 字")
    background: str = Field(description="角色背景故事，100-200 字")
    tags: list[str] = Field(description="领域标签，如 ['科学', '人文']")
    avatar_suggestion: str = Field(description="推荐头像描述，用于 Stable Diffusion prompt")

class RoleFactory:
    async def generate(self, seed_text: str, existing_profile: dict | None = None) -> GeneratedRole:
        """从种子文字 + 已有属性 生成完整角色"""
```

实现：通过 `instructor` + `GeneratedRole` Pydantic → LLM 一次性生成全部字段。属性维度再通过现有 `analyze_character()` 单独分析。

#### Scenario: 一键生成
- **WHEN** 用户在创建角色窗口输入"一个喜欢数学的害羞女孩" → 点击"AI 生成"
- **THEN** 系统自动填入角色名、描述、背景、10 维属性、领域标签、头像建议

### Requirement: P5-R2 — 知识域约束前置注入
The system SHALL 将角色的 `allowed_domains` 注入 system prompt 的 XML 区块 `{{ domain_constraint }}`，而非在回复后再过滤。

```xml
{{ domain_constraint }}
<knowledge_domains>
{% if allowed_domains %}
你是{{ persona_name }}，你只了解以下领域的知识：{{ allowed_domains | join(", ") }}。
如果用户问的问题超出你的知识范围，用角色性格自然回应即可。
{% endif %}
</knowledge_domains>
```

#### Scenario: 领域约束生效
- **WHEN** 角色标签为 `["文学", "历史"]`，用户问"你知道量子力学吗？"
- **THEN** LLM 回复应体现出角色对科学话题的回避或无知（由 System Prompt 约束），而非被 KnowledgeFilter 后处理后剪掉

### Requirement: P5-R3 — RoleData 模型增强
修改 [RoleData.cs](file:///d:/Desktop/MISS/miss-desktop-wpf/Models/RoleData.cs)，新增字段：

```csharp
public class RoleData
{
    // 现有字段（不变）
    public string Name { get; set; } = "";
    public string Description { get; set; } = "";
    public string Background { get; set; } = "";
    public MISSProfile Profile { get; set; } = new();
    public string AvatarPath { get; set; } = "";
    
    // Phase 5 新增
    public string Id { get; set; } = Guid.NewGuid().ToString("N")[..8];
    public List<string> Tags { get; set; } = new();
    public DateTime CreatedAt { get; set; } = DateTime.Now;
    
    // Phase 6 新增
    public string VoicePreset { get; set; } = "";
}
```

#### Scenario: 模型增强
- **WHEN** 生成或创建角色后
- **THEN** `RoleData` 含有关联 ID、创建时间戳、领域标签、语音预设

### Requirement: P5-R4 — CreateRoleWindow 增强
- 新增"🤖 AI 一键生成"按钮（调用 `PythonBridge.GenerateRole(seed_text)`）
- 新增领域选择器（`MultiSelectComboBox` 或 CheckBox 列表）

## Phase 6 ADDED Requirements

### Requirement: P6-R1 — Edge TTS 引擎
The system SHALL 提供基于 Edge TTS 的语音合成能力。

选型理由：Edge TTS 免费、无 API Key 需求、支持 100+ 音色、Python 库成熟（`edge-tts`）。

```python
# services/tts_engine.py
import edge_tts

class TTSEngine:
    VOICE_MAP = {
        "zh-CN-XiaoxiaoNeural": "晓晓（女·温柔）",
        "zh-CN-YunxiNeural": "云希（男·青年）",
        "zh-CN-YunyangNeural": "云扬（男·新闻）",
        "zh-CN-XiaoyiNeural": "晓依（女·活泼）",
        "ja-JP-NanamiNeural": "七海（日语·女）",
    }
    
    async def synthesize(self, text: str, voice: str = "zh-CN-XiaoxiaoNeural") -> bytes:
        """文本 → MP3 音频字节流"""
```

#### Scenario: TTS 播放
- **WHEN** 用户点击消息气泡旁的 🔊 按钮
- **THEN** C# 调用 `POST /api/tts/synthesize` → 拿到 MP3 流 → NAudio 播放

### Requirement: P6-R2 — C# AudioPlayer 组件
```csharp
// Services/AudioPlayer.cs
public static class AudioPlayer
{
    public static async Task PlayAsync(byte[] mp3Data);
    public static void Stop();
    public static bool IsPlaying { get; }
}
```

使用 NAudio NuGet 包（纯托管，支持 MP3 解码）。

#### Scenario: 播放控制
- **WHEN** 正在播放上一段音频时用户再次点击 🔊
- **THEN** 停止当前播放 → 开始播放新音频

### Requirement: P6-R3 — 角色音色绑定
- `RoleData.VoicePreset` 字段在角色编辑时可选
- 每个消息气泡的 🔊 按钮使用 `CurrentRole.VoicePreset` 构建 TTS 请求

---

### Requirement: P6-R4 — AI 角色头像生成（竞品对标补齐）
The system SHALL 通过调用 DALL·E / SD WebUI / CivitAI API 生成角色头像，并在 `RoleFactory.generate()` 返回的 `avatar_suggestion` 字段中自动生成 Stable Diffusion prompt。

选型理由：竞品对标报告显示 **所有活跃竞品都有头像/Avatar**（Live2D 或静态图），MISS 当前只能显示默认占位图——这是交互沉浸感的最低配置缺失。

实现：轻量级方案——使用 OpenAI `dall-e-3` API（`PythonBridge` 已有 `api_key`）生成 256x256 PNG。不追 Live2D（竞品报告 P2 决策：资源黑洞）。

#### Scenario: 头像生成
- **WHEN** 用户在创建角色窗口点击"AI 一键生成" → 生成角色后自动调用 DALL·E 生成头像
- **THEN** 角色头像自动填充，存入 `%APPDATA%/MISS/avatars/{roleId}.png`

## Phase 5+6 Technical Notes

| 技术点 | 决策 | 理由 |
|--------|------|------|
| 角色生成 | `instructor` + Pydantic + LLM | 与现有 llm_caller.py 统一 |
| TTS 引擎 | Edge TTS（`edge-tts` pip） | 免费·离线·无 API Key·100+ 音色 |
| 头像生成 | DALL·E 3 API | 复用现有 api_key · 不追 Live2D（竞品 P2 决策）|
| 音频播放 | NAudio NuGet | 纯托管 .NET 音频库·MP3 原生支持 |
| 领域约束 | System Prompt 前置注入 | 比以前的后处理过滤更自然 |
| 角色识别 | 8 位 UUID | 简洁·冲突概率低·人类可读 |

## Phase 5+6 Task Count

| Phase | 任务数 | 子任务数 | 新增文件 |
|-------|--------|---------|---------|
| Phase 5 | 5 | 18 | 3 |
| Phase 6 | 4 | 13 | 3 |
| **合计** | **9** | **31** | **6** |
