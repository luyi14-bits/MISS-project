# Tasks

- [x] Task 1: TavernAI Card PNG 解析器
  - [x] SubTask 1.1: 创建 `Services/TavernCardParser.cs` → `ParseFromPng(string path)` 方法
  - [x] SubTask 1.2: 解析 PNG tEXt chunk "ccv3" → base64 decode → UTF8 JSON
  - [x] SubTask 1.3: 反序列化为 `TavernCardV3` 强类型类
  - [ ] SubTask 1.4: 测试：用社区角色卡 PNG 验证解析正确

- [x] Task 2: MISS → ST 角色卡导出
  - [x] SubTask 2.1: 创建 `Services/TavernCardExporter.cs` → `ExportToPng(RoleData, path)` 方法
  - [x] SubTask 2.2: `RoleData` → `TavernCardV3` 字段映射（Description→description, Background→scenario, etc.）
  - [x] SubTask 2.3: JSON → base64 → 嵌入 1x1 PNG → tEXt chunk "ccv3"
  - [ ] SubTask 2.4: 测试：导出后在 SillyTavern 中导入验证成功

- [x] Task 3: RoleData ST 字段扩展
  - [x] SubTask 3.1: `RoleData.cs` 新增 6 个字段（TavernDescription, TavernPersonality, TavernScenario, TavernFirstMessage, TavernCreator, TavernCharacterVersion）
  - [x] SubTask 3.2: LocalStore 自动适配新字段

- [x] Task 4: CreateRoleWindow 导入按钮
  - [x] SubTask 4.1: 新增"导入 ST 角色卡" Button（`OpenFileDialog *.png`）
  - [x] SubTask 4.2: 解析成功 → 自动填充表单 + StatusText 反馈
  - [x] SubTask 4.3: 解析失败 → `NotificationService.Error("不是有效的 TavernAI 角色卡")`

- [x] Task 5: RoleSidebar 导出按钮
  - [x] SubTask 5.1: 工具栏新增"🎴 导出 ST 角色卡" Button
  - [x] SubTask 5.2: 调用 `TavernCardExporter.ExportToPng(currentRole, savePath)`
  - [x] SubTask 5.3: 导出成功 → `NotificationService.Info("已导出 ST 角色卡")`

# Task Dependencies
- Task 2 依赖 Task 1（导出需要先有 TavernCardV3 模型）
- Task 4 依赖 Task 1（导入需要解析器）
- Task 3 可并行
- Task 5 依赖 Task 2

# 工时估算
| Task | 子任务数 | 估算人天 |
|------|---------|---------|
| Task 1 (解析器) | 4 | 1.0 |
| Task 2 (导出) | 4 | 0.5 |
| Task 3 (模型扩展) | 2 | 0.3 |
| Task 4 (导入按钮) | 3 | 0.5 |
| Task 5 (导出按钮) | 3 | 0.3 |
| **合计** | **16** | **2.6** |
