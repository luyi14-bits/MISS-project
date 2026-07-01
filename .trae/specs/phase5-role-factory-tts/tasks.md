# Tasks

## Phase 5: 角色 Factory + 知识域约束

- [ ] Task 1: RoleData 模型增强
  - [ ] SubTask 1.1: `Models/RoleData.cs` 新增 `Id` (string) + `Tags` (List\<string>) + `CreatedAt` (DateTime) + `VoicePreset` (string)
  - [ ] SubTask 1.2: `LocalStore.SaveRole/LoadRole` 适配新字段（LiteDB BSON 映射）
  - [ ] SubTask 1.3: `CreateRoleWindow.xaml` 新增领域选择器（CheckBox 列表：科学/人文/艺术/技术）

- [ ] Task 2: RoleFactory LLM 一键生成
  - [ ] SubTask 2.1: 创建 `services/role_factory.py` → `GeneratedRole(BaseModel)` + `RoleFactory.generate(seed_text)`
  - [ ] SubTask 2.2: 在 `services/__init__.py` 导出 `RoleFactory`
  - [ ] SubTask 2.3: `desktop_bridge.py` 新增 `generate_role(seed_text)` → 调 `RoleFactory.generate()`
  - [ ] SubTask 2.4: `PythonBridge.cs` 新增 `GenerateRole(string seed)` 方法

- [ ] Task 3: KnowledgeDomainEngine 前置注入
  - [ ] SubTask 3.1: 创建 `services/knowledge_domain.py` → `KnowledgeDomainEngine.build_domain_prompt(tags)` → Jinja2 变量
  - [ ] SubTask 3.2: `prompt_builder.py` 新增 `{{ domain_constraint }}` 区块，注入 `allowed_domains` 上下文
  - [ ] SubTask 3.3: `PromptBuilder.build_full()` 增加 `allowed_domains` 参数
  - [ ] SubTask 3.4: `desktop_bridge.py` 传 `profile.allowed_domains` 给 `build_full()`

- [ ] Task 4: CreateRoleWindow UI 增强
  - [ ] SubTask 4.1: 新增"🤖 AI 一键生成" Button → 调 `PythonBridge.GenerateRole()` → 自动填充表单
  - [ ] SubTask 4.2: 生成中 loading 态（Button disabled + 文字"生成中…"）
  - [ ] SubTask 4.3: 生成失败 → `NotificationService.Error`

- [ ] Task 5: pytest + dotnet 验证
  - [ ] SubTask 5.1: 新增 `tests/test_role_factory.py`（3 项：正常生成 + 空 seed + 长 seed）
  - [ ] SubTask 5.2: 新增 `tests/test_knowledge_domain.py`（2 项：领域 prompt 生成 + 空标签降级）
  - [ ] SubTask 5.3: dotnet build 0 error + pytest 全量（基线 190+）

## Phase 6: TTS 语音集成

- [ ] Task 6: TTS 引擎（Python 侧）
  - [ ] SubTask 6.1: pip install `edge-tts`
  - [ ] SubTask 6.2: 创建 `services/tts_engine.py` → `TTSEngine` 抽象基类 + `EdgeTTSEngine` 实现
  - [ ] SubTask 6.3: `EdgeTTSEngine` 代码注释标注"依赖微软 Edge TTS 非官方 WebSocket 端点，未来可能需要迁移"
  - [ ] SubTask 6.4: 创建 `routers/tts.py` → `POST /api/tts/synthesize`（body: `{text, voice}` → response: `audio/mpeg` stream）
  - [ ] SubTask 6.5: `desktop_bridge.py` 新增 `tts_speak(text, voice)` → 同步封装返回 MP3 bytes

- [ ] Task 7: C# AudioPlayer
  - [ ] SubTask 7.1: NuGet 安装 `NAudio`
  - [ ] SubTask 7.2: 创建 `Services/AudioPlayer.cs` → `PlayAsync(byte[] mp3)` / `Stop()` / `IsPlaying`
  - [ ] SubTask 7.3: `PythonBridge.cs` 新增 `TtsSpeak(string text, string voice)` → 调用 desktop_bridge.tts_speak

- [ ] Task 8: ConversationView 播放按钮
  - [ ] SubTask 8.1: `ConversationView.xaml` 每个 MISS 消息气泡旁新增 🔊 Button（20x20，透明背景）
  - [ ] SubTask 8.2: Button Click → 调 `PythonBridge.TtsSpeak(text, voice)` → `AudioPlayer.PlayAsync(mp3Data)`
  - [ ] SubTask 8.3: 消息气泡组绑定 `VoicePreset`（从 `CurrentRole.VoicePreset`）

- [ ] Task 9: pytest + dotnet 验证
  - [ ] SubTask 9.1: 新增 `tests/test_tts_engine.py`（1 项：Edge TTS 可用性检查）
  - [ ] SubTask 9.2: dotnet build 0 error + pytest 全量

- [ ] Task 10: AI 头像生成（P6-R4）
  - [ ] SubTask 10.1: Python 侧 `services/avatar_generator.py` → `generate_avatar(prompt, role_id)` → 调 OpenAI DALL·E 3 API → 256x256 PNG → 存入 `%APPDATA%/MISS/avatars/{role_id}.png`
  - [ ] SubTask 10.2: `Pillow` 处理图片缩放/格式转换
  - [ ] SubTask 10.3: `desktop_bridge.py` 新增 `generate_avatar(seed_text, role_id)` → 返回头像本地路径
  - [ ] SubTask 10.4: `RoleFactory.generate()` 最后一步调 `generate_avatar()` → `RoleData.AvatarPath` 自动填充
  - [ ] SubTask 10.5: `CreateRoleWindow` 生成成功后 → `AvatarPath` 绑定到 Image 控件

- [ ] Task 11: 打包与依赖审计（package-audit-pm.md）
  - [ ] SubTask 11.1: `PyInstaller spec` 加 `--collect-all pydantic`（修复 pydantic-core 丢失）
  - [ ] SubTask 11.2: `PyInstaller spec` 加 `Pillow` C 扩展 hook（`--collect-all PIL`）
  - [ ] SubTask 11.3: `pip install edge-tts` 加入 `requirements.txt`
  - [ ] SubTask 11.4: `pip install Pillow` 加入 `requirements.txt`（头像生成依赖）
  - [ ] SubTask 11.5: 运行 `pipdeptree` 检查 instructor 依赖树——确认无 `anthropic` SDK 误入
  - [ ] SubTask 11.6: `.csproj` NuGet 引用确认 `NAudio` + `LiteDB` 版本锁定

# Task Dependencies
- Task 2 依赖 Task 1（RoleFactory 生成的 RoleData 需要新字段）
- Task 3 可并行于 Task 2
- Task 4 依赖 Task 2
- Task 6 无依赖
- Task 7 无依赖
- Task 8 依赖 Task 6 + Task 7
- Phase 5 和 Phase 6 可完全并行
- Task 10 依赖 Task 2（头像生成需要 RoleFactory 先跑完）
- Task 11 依赖 Task 6 + 10（打包审计需在全部依赖安装后跑）

# 工时估算
| Task | 子任务数 | 估算人天 |
|------|---------|---------|
| Task 1 (RoleData 增强) | 3 | 0.5 |
| Task 2 (RoleFactory) | 4 | 1.5 |
| Task 3 (KnowledgeDomain) | 4 | 1.0 |
| Task 4 (UI 增强) | 3 | 0.5 |
| Task 5 (测试) | 3 | 0.5 |
| Task 6 (TTS 引擎) | 4 | 1.5 |
| Task 7 (AudioPlayer) | 3 | 1.0 |
| Task 8 (播放按钮) | 3 | 0.5 |
| Task 9 (测试) | 2 | 0.5 |
| Task 10 (头像生成) | 5 | 1.0 |
| Task 11 (打包审计) | 6 | 0.5 |
| **合计** | **40** | **9.0** |
