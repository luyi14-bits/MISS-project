# 角色创建保存 + UI 修复 Spec

## Why
用户自建角色第二次创建时报"LLM返回异常"导致保存失败；属性面板中人物背景输入栏位置不当；"预设"命名应统一改为"角色"。

## What Changes
- 修复 `routers/character.py` 中 `_get_client()` 的 base_url 残留 bug，使第二次创建不再出错
- 从属性面板中移除"人物背景" textarea，仅保留新建弹窗中的背景输入
- 将 `index.html` 中所有"预设"文案改为"角色"
- 新建角色弹窗创建成功后自动填充侧边栏属性面板并保存到数据库

## Impact
- Affected specs: 角色创建流程、预设 CRUD
- Affected code: `routers/character.py`, `frontend/index.html`

---

## MODIFIED Requirements

### Requirement: 重复创建角色不再失败
The system SHALL 允许用户连续多次通过弹窗创建角色，每次均能正常调用 LLM 分析并保存。

#### Scenario: 第二次创建角色成功
- **WHEN** 用户第一次通过弹窗成功创建角色后，再次点击 [+] 并输入新的角色描述
- **THEN** LLM 分析成功返回属性值，角色保存到数据库，侧边栏出现新角色卡片

### Requirement: 人物背景输入仅存在于创建弹窗
The system SHALL 仅在新建角色弹窗中提供人物背景输入，属性调节面板中不包含该输入项。

#### Scenario: 属性面板无背景输入
- **WHEN** 用户打开侧边栏属性面板
- **THEN** 面板中仅显示 10 个属性滑块，不显示"人物背景" textarea

#### Scenario: 创建弹窗包含背景输入
- **WHEN** 用户点击 [+] 打开新建角色弹窗
- **THEN** 弹窗中包含角色名称、角色描述、人物背景三个输入项

### Requirement: 文案统一为"角色"
The system SHALL 将界面所有"预设"文案改为"角色"，包括侧边栏标题、按钮 tooltip、JS 代码中的默认值和 prompt 文本。

#### Scenario: 侧边栏显示"角色"
- **WHEN** 用户查看侧边栏预设/角色区域
- **THEN** 标题显示为"角色"，按钮 tooltip 显示"新建角色""保存当前角色""导入角色文件"
