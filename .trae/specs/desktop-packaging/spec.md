# MISS 桌面版 Spec — Tauri 前端 + FastAPI 后端

## Why
当前 MISS 是 Web 页面 + 命令行启动，需做成独立 .exe 桌面程序。角色/预设应保存在用户客户端本地，不再依赖后端数据库。后端仅负责 LLM 对话。

## What Changes
- **BREAKING** 架构拆分：FastAPI 后端退化为纯 LLM 对话服务，角色/预设 CRUD 迁移至 Tauri 前端本地存储
- 新增 `miss-desktop/` 目录：Tauri 项目（Rust 壳 + 前端 HTML/JS）
- 前端数据：角色/预设存入 Tauri 本地 SQLite（或 IndexedDB），不再调 `/api/preset/*`
- 后端简化：`routers/preset.py` 继续保留以兼容旧 Web 版，但桌面版不依赖
- 打包产物：`miss-desktop/src-tauri/target/release/miss.exe`

## Impact
- Affected specs: 角色创建流程、预设 CRUD
- Affected code: `miss-desktop/` (新建), `miss-backend/` (不动)
- 旧 Web 版：继续可用 (`http://127.0.0.1:8000`)，不受影响

---

## ADDED Requirements

### Requirement: Tauri 桌面壳
The system SHALL 提供一个原生 Windows 窗口应用，启动时自动 spawn FastAPI 后端进程，并在窗口内展示聊天界面。

#### Scenario: 启动流程
- **WHEN** 用户双击 `miss.exe`
- **THEN** Tauri 窗口打开，自动在后台启动 uvicorn (127.0.0.1:8000)，前端轮询 /health 直到就绪，然后显示聊天界面

#### Scenario: 关闭窗口
- **WHEN** 用户关闭 Tauri 窗口
- **THEN** 后端 uvicorn 进程自动终止，不残留后台

### Requirement: 角色/预设本地存储
The system SHALL 将所有角色数据保存在用户客户端本地，不依赖后端数据库。

#### Scenario: 创建角色保存
- **WHEN** 用户在弹窗中创建角色并点击生成
- **THEN** 调 `/api/character/analyze` 获取属性 → 角色数据写入 Tauri 本地存储 → 侧边栏出现新角色卡片

#### Scenario: 角色持久化
- **WHEN** 用户关闭并重新打开 miss.exe
- **THEN** 之前创建的所有角色仍出现在侧边栏

#### Scenario: 导出/导入
- **WHEN** 用户点击导出角色
- **THEN** 角色数据导出为 .json 文件保存到本地
- **WHEN** 用户点击导入角色
- **THEN** 选择 .json 文件后可导入角色

### Requirement: 聊天对话
The system SHALL 通过 localhost HTTP 与 FastAPI 后端通信完成 LLM 对话。

#### Scenario: 发送消息
- **WHEN** 用户在输入框输入文字并发送
- **THEN** Tauri 前端调 `POST http://127.0.0.1:8000/api/chat` → 渲染回复

---

## MODIFIED Requirements

### Requirement: 后端仅负责 LLM 对话
修改前：后端承担角色保存 + LLM 对话。修改后：后端仅保留 Chat + Character Analyze 两个核心 API，角色存储完全由前端本地接管。

##### Scenario: 后端接口保留
- **WHEN** Tauri 前端调 `/api/chat` 或 `/api/character/analyze`
- **THEN** FastAPI 正常响应，数据库相关路由可以保留但桌面版不调用

---

## REMOVED Requirements
无。旧 Web 版功能均保留，仅桌面版不依赖 `/api/preset/*` 路由。
