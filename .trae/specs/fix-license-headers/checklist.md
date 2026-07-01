# Checklist

## Task 1: Python 版权头补全
- [ ] `miss-backend/` 下所有 `.py` 文件头部包含 `SPDX-License-Identifier: AGPL-3.0-or-later`
- [ ] `tests/data/` 下的测试数据 `.py` 文件不被修改
- [ ] 注入后 `python -m py_compile` 全部通过
- [ ] 注入后 `pytest` 全量 190/190 无回归
- [ ] 文件 `__init__.py` 的版权头与文档注释不冲突

## Task 2: C# 版权头补全
- [ ] `miss-desktop-wpf/` 下所有 `.cs` 文件头部包含 `SPDX-License-Identifier: AGPL-3.0-or-later`
- [ ] `obj/` 下的自动生成 `.cs` 文件不被修改
- [ ] 注入后 `dotnet build` 0 error 0 warning
- [ ] XAML code-behind `.xaml.cs` 文件版权头位置正确

## Task 3: .gitignore 修正
- [ ] `*.spec` → `*.PyInstaller.spec`
- [ ] `spec.md` 可正常 `git add` 和 `git commit`

## 验收
- [ ] 80 个源文件 100% 覆盖 SPDX 版权头
- [ ] `dotnet build` 0 error
- [ ] `pytest` 190/190
- [ ] `git diff --stat` 仅包含注释新增行（无逻辑代码变更）
