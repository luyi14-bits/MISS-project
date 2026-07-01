# Tasks

- [ ] Task 1: Python 版权头补全（54 文件）
  - [ ] SubTask 1.1: 编写 PowerShell 批量注入脚本
    - 遍历 `miss-backend/` 下所有 `.py` 文件（排除 `tests/data/` 子目录）
    - 已有 `Copyright.*MISS Project` 的文件跳过
    - 注入 4 行（3 行版权头 + 1 空行分隔）
  - [ ] SubTask 1.2: 执行注入
    - 运行 PowerShell，确认成功覆盖 50+ 文件
  - [ ] SubTask 1.3: 语法验证
    - `python -m py_compile` 对每个修改文件编译
    - `pytest` 全量 190/190 无回归

- [ ] Task 2: C# 版权头补全（26 文件）
  - [ ] SubTask 2.1: 编写 PowerShell 批量注入脚本
    - 遍历 `miss-desktop-wpf/` 下所有 `.cs` 文件（排除 `obj/`）
    - 已有 `SPDX-License-Identifier: AGPL` 的文件跳过
    - 注入 4 行（3 行版权头 + 1 空行分隔）
  - [ ] SubTask 2.2: 执行注入
    - 运行 PowerShell，确认成功覆盖 20+ 文件
  - [ ] SubTask 2.3: 编译验证
    - `dotnet build` 0 error

- [ ] Task 3: .gitignore 修正
  - [ ] SubTask 3.1: `*.spec` → `*.PyInstaller.spec`
    - 确认 `fix-license-headers/spec.md` 可正常 git add

# Task Dependencies
- Task 1 和 Task 2 可并行（互不依赖）
- Task 3 可与 Task 1/2 并行

# 工时估算
| Task | 子任务数 | 估算人天 |
|------|---------|---------|
| Task 1 | 3 | 0.2 |
| Task 2 | 3 | 0.2 |
| Task 3 | 1 | 0.05 |
| **合计** | **7** | **0.45** |
