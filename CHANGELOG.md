# Changelog

All notable changes to MISS will be documented in this file.

## [Beta v0.7] — 2026-07-13

### Added
- **多人角色房间**: 后端 `routers/room.py`（POST /api/room/chat + stream）+ `room_bridge.py` C# 桥接 + `prompt_builder.build_room_prompt()` 房间感知上下文；C# 端 `PythonBridge.RoomChat()` + MainViewModel 房间模式 + RoleSidebar「🏠 加入当前房间」按钮
- **Beta v0.7 规划文档**: 多人角色房间 + 角色进阶 + 插件预留 Spec

### Fixed
- **DeepSeek 流式沉默失败**: 5 项修复（config deepseek_skip_instructor、chat router 流式检测、llm_caller raw 调用路径、memory_manager/prompt_builder 兼容）
- **DeepSeek 非流式 instructor 跳过**: `_call_raw` 方法，非流式请求也跳过 instructor 包装
- **Publish 安全清理**: 移除 PDB 调试符号 + DB 残留文件（miss.db / miss.db-shm / miss.db-wal）

### Security
- **增量安全审计 N01-N13**: 13 项隐患修复
  - Phase A: publish 清理 .pdb / .db（发布阻塞项）
  - Phase B: frontend-desktop localStorage→sessionStorage（6处）、frontend/index.html localStorage→sessionStorage（4处）、room_bridge except→logger、characters max_length=8、room.py Schema 校验、prompt_builder 无裸 pass、acceptance 测试更新
- **累计安全修复**: 51/51（原 38 + 增量 13），安全等级 A

### Changed
- Session 模型新增 `room_type` + `room_roles` 字段
- `main.py` 注册 room_router
- RoleSidebar 新增房间模式按钮
- 想法池 6→3（多人角色房间已交付；角色进阶 + 插件预留进入规划）

### Technical
- 新增后端文件: `routers/room.py` (168行), `services/room_bridge.py` (155行)
- 新增 C# 代码: `PythonBridge.cs` RoomChat (+64行), `MainViewModel.cs` (+27行)
- 新增 Spec: `.trae/specs/multi-character-room/` (spec + checklist + tasks)

## [Beta v0.6] — 2026-07-09

### Added
- **对话导出**: JSON/HTML/Markdown 三种格式，ConversationView 📥 按钮
- **语音输入 STT**: Whisper.net ggml-tiny 离线语音转文字，🎤 按钮按住说话/松开识别
- **SillyTavern 卡片兼容**: TavernCardParser(ccv3) + Exporter(PNG) + 导入/导出 UI
- **C# xUnit 测试基础设施**: 9 个核心域测试（9/9 PASS）
- **AudioRecorder**: NAudio 麦克风捕获 → 16kHz WAV

### Changed
- RoleData 新增 6 个 ST 兼容字段
- ConversationView 重构输入栏布局（新增 🎤 和 📥 按钮）
- 想法池 8→6（对话导出 + STT 从想法池交付）

### Technical
- 新增 NuGet: `Whisper.net` 1.9.1
- 新增项目: `miss-desktop-wpf.Tests` (xunit + coverlet)
- 新增服务: `ConversationExporter`, `AudioRecorder`, `WhisperSttService`, `TavernCardParser`, `TavernCardExporter`
- 新增服务合计 6 文件 769 行 C#

## [Beta v0.5] — 2026-07-08
