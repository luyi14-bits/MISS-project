# Checklist

## Task 1: RoleData 模型增强
- [ ] `RoleData.cs` 含 `Id` (string) 字段
- [ ] `RoleData.cs` 含 `Tags` (List\<string>) 字段
- [ ] `RoleData.cs` 含 `CreatedAt` (DateTime) 字段
- [ ] `RoleData.cs` 含 `VoicePreset` (string) 字段
- [ ] `LocalStore.SaveRole/LoadRole` 正确读写新字段
- [ ] `CreateRoleWindow.xaml` 有领域选择器（至少 4 个 CheckBox：科学/人文/艺术/技术）

## Task 2: RoleFactory LLM 一键生成
- [ ] `services/role_factory.py` 存在，含 `GeneratedRole(BaseModel)` + `RoleFactory` 类
- [ ] `desktop_bridge.py` `generate_role(seed_text)` 可正常调用
- [ ] `PythonBridge.GenerateRole(seed)` C# 方法存在
- [ ] 种子文字"喜欢数学的害羞女孩" → 返回完整 `RoleData`（含 name/desc/background/tags）
- [ ] 生成失败 → 返回 `{"_error": True, "message": "..."}`

## Task 3: KnowledgeDomainEngine 前置注入
- [ ] `services/knowledge_domain.py` 存在，含 `build_domain_prompt(tags)` 方法
- [ ] `prompt_builder.py` 模板含 `{{ domain_constraint }}` 区块
- [ ] `build_full()` 接收 `allowed_domains` 参数
- [ ] 角色标签 `["文学", "历史"]` → system prompt 含 `知识范围：文学, 历史`
- [ ] 角色无标签 → system prompt 不含领域约束

## Task 4: CreateRoleWindow UI 增强
- [ ] "🤖 AI 一键生成" 按钮存在
- [ ] 生成中按钮 disabled + 显示"生成中…"
- [ ] 生成成功 → 表单自动填充
- [ ] 生成失败 → `NotificationService.Error` 弹出

## Task 5: pytest 验证（Phase 5）
- [ ] `tests/test_role_factory.py` 存在（≥3 项测试）
- [ ] `tests/test_knowledge_domain.py` 存在（≥2 项测试）
- [ ] dotnet build 0 error
- [ ] pytest 全量通过

## Task 6: TTS 引擎
- [ ] `pip install edge-tts` 成功
- [ ] `services/tts_engine.py` 存在，含 `TTSEngine.synthesize(text, voice)`
- [ ] `routers/tts.py` 存在，含 `POST /api/tts/synthesize`
- [ ] 请求 `{"text": "你好", "voice": "zh-CN-XiaoxiaoNeural"}` → 返回 `audio/mpeg` 流
- [ ] `desktop_bridge.py` 含 `tts_speak(text, voice)` 方法

## Task 7: C# AudioPlayer
- [ ] NuGet `NAudio` 已安装
- [ ] `Services/AudioPlayer.cs` 存在，含 `PlayAsync()` / `Stop()` / `IsPlaying`
- [ ] `PythonBridge.TtsSpeak(text, voice)` 方法存在
- [ ] 播放 MP3 正常（有声音输出）

## Task 8: ConversationView 播放按钮
- [ ] 每个 MISS 消息气泡旁有 🔊 按钮
- [ ] 点击 🔊 → 调用 `PythonBridge.TtsSpeak(text, voice)` → `AudioPlayer.PlayAsync(mp3Data)`
- [ ] 连续点击两个消息的 🔊 → 第一个停止，第二个播放

## Task 9: pytest 验证（Phase 6）
- [ ] `tests/test_tts_engine.py` 存在（≥1 项测试）
- [ ] dotnet build 0 error
- [ ] pytest 全量通过

## 验收
- [ ] 输入种子文字 → 一键生成完整角色（姓名+描述+背景+领域标签+属性）
- [ ] 角色领域标签生效 → LLM 回避非领域话题
- [ ] 点击 🔊 → 播放角色语音
- [ ] dotnet build 0 error
- [ ] pytest 全量通过
