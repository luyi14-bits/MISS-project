# Git 仓库安全审计报告 — G1-G3

> **审查日期**：2026-06-28
> **审查人**：安全专家组（SDL · Web 安全 · 二进制安全）
> **仓库**：`origin git@github.com:luyi14-bits/MISS-project.git`
> **分支**：master · 2 commits

---

## 一、总体评估

| 维度 | 状态 | 说明 |
|------|------|------|
| 敏感文件泄露 | ✅ 干净 | 无 `.pdb` `.exe` `.db` `.sqlite3` `.env` `.toc` 进入 Git |
| 构建产物污染 | ✅ 干净 | `obj/` `bin/` `dist/` `build/` `publish/` 全部被 `.gitignore` 排除 |
| 二进制文件 | ⚠️ 1 处 | `docs/AI伴侣系统提示词架构设计_完整版.docx` — Word 含元数据 |
| 作者身份 | 🔴 2 处暴露 | GitHub 用户名 + Gmail 明文在 commit author 和 remote URL 中 |
| 临时文件污染 | ⚠️ 1 处 | `_wpftmp.csproj` — VS WPF 临时热重载文件不应提交 |
| 文档死链接 | 🟡 3 处 | `file:///d:/Desktop/MISS/` 绝对路径暴露开发机结构 |
| `.gitignore` 覆盖 | ⚠️ 待提交 | 阶段 5 (D9) 新增的 10 条排除规则已写入文件但**未 commit** |

**综合评级**：B+（2 项需修复 + 1 项待提交 + 接受 1 项现实约束）

---

## 二、逐项发现

### G1 — Git 作者身份完全暴露 🔴

**发现位置**：

```
$ git log --all --pretty=format:"%h %ai %an <%ae> %s"

b507399 2026-06-28 21:26:37 +0800 luyi14-bits <luyi14bits@gmail.com> ...
a54e113 2026-06-28 20:20:53 +0800 luyi14-bits <luyi14bits@gmail.com> ...
```

```
$ git remote -v

origin  https://github.com/luyi14-bits/MISS-project.git (fetch)
origin  https://github.com/luyi14-bits/MISS-project.git (push)
```

| 暴露项 | 值 | 风险 |
|--------|-----|------|
| GitHub 用户名 | `luyi14-bits` | 可直接定位到作者 GitHub 主页 |
| 邮箱 | `luyi14bits@gmail.com` | 明文 Gmail，可被搜索引擎索引 |
| 仓库名 | `MISS-project` | 完全公开 |
| Remote URL | HTTPS（非 SSH） | 需要 Personal Access Token 才能 push |

**CVSS 3.1**: 信息性（非代码漏洞，但身份泄露风险）

**修复方案**：

```bash
# 方案 A（推荐）：使用 GitHub noreply 邮箱
git config user.email "luyi14-bits@users.noreply.github.com"

# 方案 B：使用 GitHub noreply ID+邮箱
git config user.email "148196215+luyi14-bits@users.noreply.github.com"

# 重写 2 个 commit 的 author 信息
git filter-branch --env-filter '
OLD_EMAIL="luyi14bits@gmail.com"
CORRECT_NAME="luyi14-bits"
CORRECT_EMAIL="luyi14-bits@users.noreply.github.com"
if [ "$GIT_COMMITTER_EMAIL" = "$OLD_EMAIL" ]
then
    export GIT_COMMITTER_NAME="$CORRECT_NAME"
    export GIT_COMMITTER_EMAIL="$CORRECT_EMAIL"
fi
if [ "$GIT_AUTHOR_EMAIL" = "$OLD_EMAIL" ]
then
    export GIT_AUTHOR_NAME="$CORRECT_NAME"
    export GIT_AUTHOR_EMAIL="$CORRECT_EMAIL"
fi
' --tag-name-filter cat -- --branches --tags

# 强制推送（⚠️ 如果仓库已有其他协作者，需协调）
git push --force --all
```

**⚠️ 风险警告**：`git filter-branch` 重写历史会改变所有 commit SHA。如果仓库已有 Star/Fork/协作者，需要评估影响。如果选择不重写，至少将 `user.email` 改为 noreply 地址以避免未来的 commit 泄露。

---

### G2 — Visual Studio 临时热重载文件污染 ⚠️

**发现位置**：

```
miss-desktop-wpf/miss-desktop-wpf_wxqpy13d_wpftmp.csproj
```

| 属性 | 值 |
|------|-----|
| 文件类型 | Visual Studio WPF 热重载临时文件 |
| 产生原因 | VS 在 XAML 编辑时自动生成 |
| 命名规则 | `{project_name}_{8-char-hex}_wpftmp.csproj` |
| 是否应该提交 | ❌ 否 — 应被 `.gitignore` 排除 |

**修复**：

```bash
# 1. 从 Git 中移除（保留本地文件）
git rm --cached miss-desktop-wpf/miss-desktop-wpf_wxqpy13d_wpftmp.csproj

# 2. 加入 .gitignore
echo "*_wpftmp*" >> .gitignore

# 3. 提交
git add .gitignore
git commit -m "chore: remove VS WPF temp file, add _wpftmp to gitignore"
```

---

### G3 — Word 文档元数据泄露 🟡

**发现位置**：

```
docs/AI伴侣系统提示词架构设计_完整版.docx
docs/指导文件.doc
docs/指导文件_extracted.txt
```

| 文件 | 大小 | 风险 |
|------|------|------|
| `.docx` | 二进制 | Microsoft Office 文档默认嵌入作者姓名、公司名、编辑历史 |
| `.doc` | 二进制 | 同上（.doc 格式元数据更丰富） |
| `_extracted.txt` | 文本 | 从 .doc 提取的纯文本内容 |

**PoC** — 任何人下载后可执行：

```powershell
# 解压 .docx（本质是 ZIP）
Expand-Archive "AI伴侣系统提示词架构设计_完整版.docx" -DestinationPath docx_meta

# 查看作者信息
Get-Content docx_meta/docProps/core.xml
# 会显示：<dc:creator>...</dc:creator> <cp:lastModifiedBy>...</cp:lastModifiedBy>
```

**修复**：

```bash
# 方案 A：从 Git 中移除（推荐 — 这些文档应放在 .gitignore 中）
git rm --cached "docs/AI伴侣系统提示词架构设计_完整版.docx"
git rm --cached "docs/指导文件.doc"
git rm --cached "docs/指导文件_extracted.txt"
echo "*.docx" >> .gitignore
echo "*.doc" >> .gitignore

# 方案 B：清除元数据后重新提交
# 在 Word 中：文件 → 信息 → 检查文档 → 检查文档属性 → 全部删除 → 另存

# 方案 C：转为 Markdown（推荐 — 去元数据 + 可 git diff）
```

---

### ✅ 确认安全项

以下审计项全部通过，无需修复：

| 检查项 | 结果 | 验证命令 |
|--------|------|----------|
| `.pdb` 调试符号 | ❌ 无 | `git ls-files \| grep "\.pdb$"` → 空 |
| `.exe` 可执行文件 | ❌ 无 | `git ls-files \| grep "\.exe$"` → 空 |
| `.db` `.sqlite3` 数据库 | ❌ 无 | `git ls-files \| grep "\.db$\|\.sqlite3$"` → 空 |
| `.env` 真实环境文件 | ❌ 无 | `git ls-files \| grep "\.env$"` → 仅 `.env.example` |
| `.pyc` 编译字节码 | ❌ 无 | `git ls-files \| grep "\.pyc$"` → 空 |
| `.toc` PyInstaller 路径 | ❌ 无 | `git ls-files \| grep "\.toc$"` → 空 |
| `obj/` `bin/` 构建产物 | ❌ 无 | `.gitignore` 已排除 ✅ |
| `build/` `dist/` 产物 | ❌ 无 | `.gitignore` 已排除 ✅ |
| `sk-` API Key 泄露 | ❌ 无 | 仅 `sk-placeholder` 占位符 |
| `access_token` 泄露 | ❌ 无 | 仅 `.env.example` 注释中的占位说明 |
| `MISS_FERNET_KEY` 泄露 | ❌ 无 | 同上 |
| `AGPL v3` LICENSE | ✅ 正确 | 已提交，版权行在源文件中 |
| `.gitignore` 覆盖范围 | ✅ 良好 | obj/bin/dist/build/publish/.db/.sqlite3/.env 全覆盖 |

---

## 三、待提交项（阶段 5 修复已写入但未 commit）

以下文件已有本地修改但未推送到远程：

| 文件 | 修改内容 | 对应阶段 |
|------|----------|----------|
| `.gitignore` | 增加 `obj/` `bin/` `*.pdb` `*.toc` `*.pkg` `*.pyz` `*_absolute.txt` `xref*.html` `*.spec` | D9 (阶段 5) |
| `build.ps1` | 完整安全打包脚本（4 阶段 + 去匿名化验证） | D1-D6 (阶段 5) |
| `frontend/index.html` | DeepSeek URL 补 `/v1` | D11 (阶段 5) |
| `frontend-desktop/app.js` | 同上 | D11 (阶段 5) |

---

## 四、修复优先级矩阵

| # | 严重程度 | 问题 | 工作量 | 风险 |
|---|----------|------|--------|------|
| G1 | 🔴 高 | Git author 邮箱明文暴露 | 5 分钟（改 config 仅对新 commit）+ 30 分钟（filter-branch 重写历史） | 重写历史会改变 SHA |
| G2 | 🟡 中 | VS _wpftmp.csproj 污染 | 2 分钟 | 无 |
| G3 | 🟡 中 | .docx/.doc 元数据泄露 | 5 分钟 | 需确认文档内容是否需保留 |

---

## 五、修复建议

### 立即执行（10 分钟，无破坏性）

```bash
# 1. 修改作者邮箱为 GitHub noreply（仅影响之后的 commit）
git config user.email "luyi14-bits@users.noreply.github.com"

# 2. 移除 _wpftmp 文件 + 加入 .gitignore
git rm --cached miss-desktop-wpf/miss-desktop-wpf_wxqpy13d_wpftmp.csproj
echo "*_wpftmp*" >> .gitignore

# 3. 移除 .docx/.doc + 加入 .gitignore
git rm --cached "docs/AI伴侣系统提示词架构设计_完整版.docx"
git rm --cached "docs/指导文件.doc"
git rm --cached "docs/指导文件_extracted.txt"
echo "*.docx" >> .gitignore
echo "*.doc" >> .gitignore

# 4. 提交所有阶段 5 修复
git add -A
git commit -m "chore: G1-G3 git security fixes + stage 5 cleanup (.pdb/.env/.db/obj/bin) + Deepeek URL fix"
git push
```

### 可选（评估影响后决定）

```bash
# 重写 2 个历史 commit 的 author 邮箱
# ⚠️ 仅当仓库无其他协作者时执行
git filter-branch -f --env-filter '
if [ "$GIT_AUTHOR_EMAIL" = "luyi14bits@gmail.com" ]
then
    export GIT_AUTHOR_EMAIL="luyi14-bits@users.noreply.github.com"
fi
if [ "$GIT_COMMITTER_EMAIL" = "luyi14bits@gmail.com" ]
then
    export GIT_COMMITTER_EMAIL="luyi14-bits@users.noreply.github.com"
fi
' HEAD
git push --force
```
