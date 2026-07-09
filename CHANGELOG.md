# Changelog

All notable changes to MISS will be documented in this file.

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
