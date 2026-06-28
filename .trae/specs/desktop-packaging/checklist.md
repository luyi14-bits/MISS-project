# Checklist

- [ ] `miss-desktop/` 目录存在且包含完整 Tauri 项目结构
- [ ] `src/index.html` 渲染 MISS 聊天界面（与旧 Web 版视觉一致）
- [ ] `src/assets/` 包含所有头像图片 + lucide.min.js + tailwind.browser.min.js
- [ ] `src/style.css` 包含所有 CSS 样式
- [ ] `src/app.js` 包含所有交互逻辑，无 `onclick="xxx()"` HTML 属性写法（Tauri CSP 限制）
- [ ] 侧边栏标题显示"角色"
- [ ] `store.js` 提供 getRoles / saveRole / deleteRole / importRole
- [ ] 创建角色弹窗 → LLM 分析 → 属性填充 → localStorage 保存 → 侧边栏出现新卡片
- [ ] 关闭重开 → 侧边栏角色卡片仍在
- [ ] ⭐ 保存按钮 → 角色写入 localStorage
- [ ] 📂 导出按钮 → 弹出系统"另存为"对话框 → 生成 .json
- [ ] 📂 导入按钮 → 弹出系统"打开文件"对话框 → 解析 .json → 写入 localStorage
- [ ] Tauri 窗口打开后自动启动 uvicorn（127.0.0.1:8000）
- [ ] 启动时显示 loading，/health 返回 200 后显示聊天界面
- [ ] 关闭 Tauri 窗口 → uvicorn 进程终止
- [ ] 对话正常：发送消息 → 显示 spoken + inner_thought
- [ ] 设置弹窗：API Key / Base URL / 模型下拉 → 保存后生效
- [ ] `miss-backend/` 已用 PyInstaller 打包为 `miss-server.exe`（嵌入 Python，`--onefile`）
- [ ] `tauri.conf.json` 中 `bundle.resources` 指向 `miss-server.exe`
- [ ] `npm run tauri build` 成功生成 `miss.exe`
- [ ] 用户端：安装后双击 → 无需安装 Python / Rust / Node.js → 聊天可用
- [ ] 旧 Web 版 `python -m uvicorn main:app` 仍正常启动

---

## 技术债务（不阻塞当前交付）

- [ ] **DEBT-1: onclick → addEventListener 迁移**：`index.html` 中约 83 处 `onclick`/`onchange`/`oninput`/`onkeydown` 内联事件 + `app.js` 中 31 个 `window.*` 全局函数，应在下一次重构中一次性迁移为 ES module + `addEventListener` 模式，同时收紧 CSP 移除 `'unsafe-inline'`。
- [ ] **DEBT-2: 文件对话框 Tauri 化**：导出/导入当前使用 Blob + `<input type="file">` 浏览器 API，后续迁移到 `tauri-plugin-dialog` 的 `save()`/`open()` 可获得原生体验。
- [ ] **DEBT-3: 新增按钮回调规范**：在 DEBT-1 完成之前，**强制要求**所有新增按钮回调必须使用 `window.xxx = function(){}` 写法挂载到全局，禁止使用 HTML `onclick` 属性或不挂 window 的 IIFE 内函数，避免作用域不可见导致按钮无响应。
