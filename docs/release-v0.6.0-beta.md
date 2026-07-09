## MISS Beta v0.6

Beta 推进中 — 本次新增 4 项功能交付，想法池 8→6。

### 新增功能

| 功能 | 技术 | 文件 |
|------|------|------|
| **SillyTavern 角色卡兼容** | TavernCardParser (ccv3) + Exporter (PNG + CRC-32) | `TavernCardParser.cs` (161行) + `TavernCardExporter.cs` (144行) |
| **语音输入 STT** | Whisper.net ggml-tiny 离线转写 | `AudioRecorder.cs` (108行) + `WhisperSttService.cs` (92行) |
| **对话导出** | JSON / HTML / Markdown 三格式 | `ConversationExporter.cs` (136行) |
| **C# xUnit 测试** | `miss-desktop-wpf.Tests` 项目 | `CoreDomainTests.cs` (128行) |

### UI 新增

- 🎴 CreateRoleWindow「📥 导入 ST 角色卡」
- 🎴 RoleSidebar「🎴 导出 ST 角色卡」
- 🎤 ConversationView「按住录音 / 松开识别」
- 📥 ConversationView「导出对话」

### 新增 NuGet

- `Whisper.net` 1.9.1
- `xunit` + `coverlet`

### 累计统计（Beta v0.6）

```
提交：35 次
pytest：~190/190
xUnit：9/9 PASS
安全：A（38/38）
Spec：10/10 + 4 v0.6 专项
想法池：6 项
Skills：8 个
标准文件：8/8
```

Contributing: read [CLA.md](https://github.com/luyi14-bits/MISS-project/blob/master/CLA.md) — PR submission is acceptance.
