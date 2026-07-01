# fix-license-headers — 全项目 SPDX 版权头补全 Spec

## Meta
- **优先级**: P1
- **估算工时**: 0.5 人天
- **影响 Spec**: 无（纯增量、无破坏性变更）
- **影响代码**: 80 个源文件（54 `.py` + 26 `.cs`）

## Why
MISS 项目根目录已有 `LICENSE` 文件（AGPL v3），但**所有 80 个源文件中没有一个包含版权声明**。AGPL 的许可证执行依赖源文件级别的声明——如果侵权者只拷贝了单个文件（如 `llm_caller.py`），该文件本身不包含任何许可证信息，法律上难以主张"对方应知"。

FSF 推荐的标准做法：每个源文件头部包含 SPDX 标识符 + Copyright 声明。

## What Changes
- 为 54 个 `miss-backend/` 下的 `.py` 文件（排除 `tests/data/`）添加 SPDX 版权头
- 为 26 个 `miss-desktop-wpf/` 下的 `.cs` 文件（排除 `obj/`）添加 SPDX 版权头
- `.gitignore` 中的 `*.spec` 排除规则改为 `*.PyInstaller.spec`（避免误排除 spec.md）

## Impact
- Affected specs: 无
- Affected code: `miss-backend/**/*.py` + `miss-desktop-wpf/**/*.cs`（80 个文件）
- 不破坏任何现有功能

---

## ADDED Requirements

### Requirement: R1 — Python 文件 SPDX 版权头
The system SHALL 在每个 `miss-backend/` 下的 `.py` 文件头部添加以下格式的版权声明（紧接 `# -*- coding: utf-8 -*-` 之后，或文件第 1 行）：

```python
# Copyright (C) 2026  MISS Project Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
```

#### Scenario: 正常 Python 文件
- **WHEN** 执行版权头注入
- **THEN** 每个 `.py` 第 1-3 行为上述三行注释
- **AND** 原有代码从第 5 行开始（空一行分隔）

#### Scenario: 已有版权头的文件跳过
- **WHEN** 文件已包含 `Copyright.*MISS Project` 匹配
- **THEN** 跳过该文件，不重复注入

### Requirement: R2 — C# 文件 SPDX 版权头
The system SHALL 在每个 `miss-desktop-wpf/` 下的 `.cs` 文件头部添加以下格式的版权声明：

```csharp
// Copyright (C) 2026  MISS Project Contributors
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
```

#### Scenario: 正常 C# 文件
- **WHEN** 执行版权头注入
- **THEN** 每个 `.cs` 第 1-3 行为上述三行注释
- **AND** 原有 `using` 语句从第 6 行开始

#### Scenario: 已有版权头的文件跳过
- **WHEN** 文件已包含 `SPDX-License-Identifier: AGPL` 匹配
- **THEN** 跳过该文件，不重复注入

### Requirement: R3 — .gitignore 修正
The system SHALL 修正 `.gitignore` 中的 `*.spec` 规则，使其不排除 `spec.md` 文件：

```diff
- *.spec
+ *.PyInstaller.spec
```

#### Scenario: spec.md 不被误排除
- **WHEN** 修正后 `.gitignore`
- **THEN** `.trae/specs/fix-license-headers/spec.md` 可正常 `git add`

### Requirement: R4 — 验收回归验证
The system SHALL 确认版权头注入不破坏任何现有功能：
- `python -m py_compile` 所有修改的 `.py` 语法通过
- `dotnet build` 0 error
- `pytest` 190/190 无回归
