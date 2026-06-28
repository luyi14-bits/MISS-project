# Tasks

- [ ] Task 1: 初始化 Tauri 项目骨架
  - [ ] SubTask 1.1: 在 `miss-desktop/` 下执行 `npm create tauri-app@latest`，选 Vanilla JS 模板
  - [ ] SubTask 1.2: 配置 `src-tauri/tauri.conf.json`：窗口标题 "MISS"、尺寸 1100×750、最小尺寸 800×500、关闭行为 exit
  - [ ] SubTask 1.3: 将现有 `frontend/index.html` 的 `<body>` 内容迁移到 `miss-desktop/src/index.html`
  - [ ] SubTask 1.4: 将 `frontend/assets/` 复制到 `miss-desktop/src/assets/`
  - [ ] SubTask 1.5: 将 `frontend/index.html` 的 `<style>` 和 `<script>` 提取为 `miss-desktop/src/style.css` 和 `miss-desktop/src/app.js`

- [ ] Task 2: 角色/预设本地存储（替代 `/api/preset/*`）
  - [ ] SubTask 2.1: 新增 `src/store.js`，封装 localStorage 读写（key: `"miss_roles"`），`getRoles()` / `saveRole(name, profile, background)` / `deleteRole(name)` / `importRole(json)`
  - [ ] SubTask 2.2: 修改 `saveCurrentPreset()`：不再调 `/api/preset/save`，改为调 `saveRole(name, appliedProfile, background)` 写本地
  - [ ] SubTask 2.3: 修改 `createPresetFromModal()`：LLM 分析成功后调 `saveRole()` 本地保存（替代 `/api/preset/save`）
  - [ ] SubTask 2.4: 修改 `loadPresets()`：不再调 `/api/preset/list`，改为从 `getRoles()` 读本地数据渲染侧边栏卡片
  - [ ] SubTask 2.5: 修改 `loadAndApplyPreset()`：不再调 `/api/preset/{id}`，改为从 `getRoles()` 按 name 查找
  - [ ] SubTask 2.6: 实现导出：调 Tauri `dialog.save()` 写 .json 文件（或 fallback `Blob` 下载）
  - [ ] SubTask 2.7: 实现导入：调 Tauri `dialog.open()` 读 .json 文件 → `importRole()`

- [ ] Task 3: 后端进程管理（Tauri Rust 端）
  - [ ] SubTask 3.1: 用 PyInstaller 将 `miss-backend/` 打包为 `miss-server.exe`（`--onefile --windowed`），嵌入 Python 运行时
  - [ ] SubTask 3.2: 在 `src-tauri/src/main.rs` 中增加 spawn 逻辑：启动同目录下的 `miss-server.exe`（或子目录 `server/miss-server.exe`）
  - [ ] SubTask 3.3: 前端启动时轮询 `http://127.0.0.1:8000/health`，就绪后隐藏 loading 显示聊天界面
  - [ ] SubTask 3.4: Tauri `on_window_event` 监听窗口关闭事件 → kill `miss-server.exe` 子进程
  - [ ] SubTask 3.5: 配置 `tauri.conf.json` 中 `bundle.resources` 将 `miss-server.exe` 嵌入安装包

- [ ] Task 4: 打包与发布
  - [ ] SubTask 4.1: 配置 `tauri.conf.json` 中 `bundle` → `identifier: "com.miss.desktop"`, `icon`, `resources: ["../server/miss-server.exe"]`
  - [ ] SubTask 4.2: 执行 `npm run tauri build` → 生成 `src-tauri/target/release/miss.exe`（自带 WebView2，不含 Python 依赖）
  - [ ] SubTask 4.3: 编写 `build/installer.nsi` (NSIS 脚本) 将 `miss.exe` + `miss-server.exe` 打包为安装包
  - [ ] SubTask 4.4: 用户端验证：安装后双击桌面快捷方式 → 自动启动 Tauri 窗口 + 后台 `miss-server.exe` → 聊天可用，无需安装 Python / Rust / Node.js

- [ ] Task 5: 验证测试
  - [ ] SubTask 5.1: 验证 Tauri 窗口打开后自动启动后端，聊天可用
  - [ ] SubTask 5.2: 验证创建角色 → 保存 → 关闭 → 重开 → 角色仍在
  - [ ] SubTask 5.3: 验证导出/导入角色 .json 文件
  - [ ] SubTask 5.4: 验证关闭窗口后 uvicorn 进程终止
  - [ ] SubTask 5.5: 验证旧 Web 版 `python -m uvicorn main:app` 仍正常

# Task Dependencies
- Task 2 依赖 Task 1（先有项目骨架才能改 JS）
- Task 3 依赖 Task 1（Tauri 项目存在才能改 Rust 端）
- Task 2 和 Task 3 可并行
- Task 4 依赖 Task 1 + Task 2 + Task 3
- Task 5 依赖 Task 4
