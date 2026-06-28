# 预设 [+]/[⭐]/[📂] 按钮无反应 — 根因分析与修复方案

> 发现日期：2026-06-26 | 优先级：高（功能完全不可用）

---

## 问题现象

在页面 http://127.0.0.1:8000 点击侧边栏预设区域三个按钮 (**+** 新建 / **⭐** 保存 / **📂** 导入) 全部无反应。

浏览器 Console 报错：
```
Uncaught ReferenceError: createPreset is not defined
```

## 根因分析

### 触发链

```
用户点击 [+] 按钮
  → onclick="createPreset()"            ← HTML 属性（运行在全局作用域）
  → 浏览器查找 window.createPreset
  → window 上不存在该函数
  → 静默失败（或 F12 Console 报 ReferenceError）
```

### 为什么不在 window 上

文件 `frontend/index.html` 的 JS 代码包裹在一个 **IIFE（立即执行函数）** 中：

```javascript
// index.html L710 → L1109
(function(){
  // ↑ 从这里开始，所有变量/函数默认都在闭包内，不污染全局

  // L851 — 没有 window. 前缀，只在 IIFE 内部可访问
  async function createPreset(){ ... }

  // L860 — 同样没有 window. 前缀
  async function saveCurrentPreset(){ ... }

  // L870 — 同样没有 window. 前缀
  function importPresetFile(){ ... }

  // L928 — 这个有 window. 前缀，所以能正常用
  window.sendMsg = function(){ ... }

})();  // ← IIFE 结束
```

HTML 的 `onclick="createPreset()"` 运行在**全局作用域**。而 `createPreset` 定义在 IIFE 闭包内，没有挂载到 `window`，所以按钮点击时找不到函数 → 无反应。

### 影响范围

| 按钮 | HTML onclick | 函数定义行 | 是否挂 window | 状态 |
|------|-------------|-----------|:---:|:--:|
| `[+]` 新建 | `onclick="createPreset()"` | L851 | ❌ | **不可用** |
| `[⭐]` 保存 | `onclick="saveCurrentPreset()"` | L860 | ❌ | **不可用** |
| `[📂]` 导入 | `onclick="importPresetFile()"` | L870 | ❌ | **不可用** |

三个按钮全部受影响。

### 附：项目中哪些函数正常工作

以下函数因为用了 `window.xxx = function(){}` 写法，所以按钮能正常调用：

```javascript
window.toggleSidebar   L724    ✅
window.switchSession   L728    ✅
window.addSession      L734    ✅
window.openSettings    L1018   ✅
window.closeSettings   L1031   ✅
window.sendMsg         L928    ✅
```

---

## 修复方案（2 选 1）

### 方案 A：逐个加 window 前缀（推荐，改动最小）

把三个函数声明从普通函数改为 `window.xxx = function()`：

> 文件：`frontend/index.html`

```javascript
// 改前 — L851
async function createPreset(){

// 改后
window.createPreset = async function(){
```

```javascript
// 改前 — L860
async function saveCurrentPreset(){

// 改后
window.saveCurrentPreset = async function(){
```

```javascript
// 改前 — L870
function importPresetFile(){

// 改后
window.importPresetFile = function(){
```

### 方案 B：末尾统一暴露

在 IIFE 结束前（L1109 的 `})();` 之前）加三行：

```javascript
  window.createPreset = createPreset;
  window.saveCurrentPreset = saveCurrentPreset;
  window.importPresetFile = importPresetFile;
})();
```

---

## 验证方法

修改后，刷新 http://127.0.0.1:8000，打开 F12 Console：

1. 输入 `typeof window.createPreset` → 应返回 `"function"`（改前返回 `"undefined"`）
2. 点击 **[+]** 按钮 → 应弹出"新角色名称"对话框
3. 点击 **[⭐]** 按钮 → 应弹出"预设名称"对话框
4. 点击 **[📂]** 按钮 → 应弹出文件选择框

---

## 补充说明

这属于典型的 **IIFE 作用域泄漏问题**。项目中有两种写法混用：
- `window.xxx = function(){}` — 按钮可用
- `function xxx(){}` — 按钮不可用（但 IIFE 内部的其他函数可以调用它们）

建议以后新增按钮回调统一使用 `window.xxx = function(){}` 写法，避免同类问题。
