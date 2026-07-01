# sillytavern-card-compat Spec — SillyTavern / TavernAI 角色卡兼容

## Why
竞品对标报告（2026-07-01）的核心发现：**SillyTavern 的角色卡格式（PNG 封装 JSON）已经是 AI 角色扮演开源社区的事实标准**。如果 MISS 能读取/导出 ST 兼容的角色卡，就能直接接入整个开源角色扮演社区的用户——不需要自己做前端、社区。这是投入产出比最高的生态动作。

## Meta
- **优先级**: P1（生态集成，非阻塞发布）
- **估算工时**: 3 人天
- **影响 Spec**: phase5-role-factory-tts（角色模型需适配 ST 字段）

## What Changes
- **新增** `Services/TavernCardParser.cs` — 解析 PNG 封装的 TavernAI Card JSON
- **新增** `Services/TavernCardExporter.cs` — 将 MISS RoleData 导出为 TavernAI Card PNG
- **增强** `RoleData.cs` — 新增 `TavernDescription` / `TavernPersonality` / `TavernScenario` / `TavernFirstMessage` 字段（ST 格式的 4 个核心角色字段）
- **增强** CreateRoleWindow — 新增"导入 ST 角色卡"按钮（`OpenFileDialog *.png`）

## Impact
- 新增: `Services/TavernCardParser.cs`, `Services/TavernCardExporter.cs`
- 修改: `Models/RoleData.cs`, `Views/CreateRoleWindow.xaml/.cs`

---

## ADDED Requirements

### Requirement: ST-R1 — 读取 ST 角色卡 PNG
The system SHALL 解析 TavernAI Card PNG 格式（PNG 文件内嵌 base64 `ccv3` tEXt chunk → JSON → 提取 name/description/personality/scenario/first_mes/creator/avatar）。

```csharp
// TavernCardParser.cs
public static TavernCardData ParseFromPng(string pngPath)
{
    // 1. 读取 PNG 文件
    // 2. 提取 tEXt chunk "ccv3"
    // 3. base64 decode → UTF8
    // 4. JsonSerializer.Deserialize<TavernCardV3>()
}
```

#### Scenario: 导入 ST 角色卡
- **WHEN** 用户在创建角色窗口点击"导入 ST 角色卡" → 选择 PNG 文件
- **THEN** 自动解析填充 name + description + personality → 可选调 AI 分析 → 创建角色

### Requirement: ST-R2 — 导出 MISS 角色为 ST 卡 PNG
The system SHALL 将 `RoleData` 导出为 TavernAI Card V3 格式 PNG。

```csharp
// TavernCardExporter.cs
public static void ExportToPng(RoleData role, string outputPath)
{
    // 1. 构建 TavernCardV3 JSON
    // 2. base64 encode
    // 3. 嵌入到 1x1 PNG + tEXt chunk "ccv3"
    // 4. 写入文件
}
```

#### Scenario: 导出 ST 角色卡
- **WHEN** 用户在角色列表右键 → "导出为 ST 角色卡"
- **THEN** 保存为 PNG 文件，可在 SillyTavern 中直接导入使用

### Requirement: ST-R3 — RoleData ST 字段扩展
仿照 ST 格式结构，新增 4 个专有字段：

```csharp
// RoleData.cs 新增
public string TavernDescription { get; set; } = "";   // ST: description — 角色外貌/背景
public string TavernPersonality { get; set; } = "";    // ST: personality — 性格摘要
public string TavernScenario { get; set; } = "";        // ST: scenario — 对话背景
public string TavernFirstMessage { get; set; } = "";    // ST: first_mes — 角色首发消息
```

#### Scenario: ST 字段保留
- **WHEN** 用户导入 ST 角色卡 → 编辑 → 导出
- **THEN** ST 专有字段往返不丢失
