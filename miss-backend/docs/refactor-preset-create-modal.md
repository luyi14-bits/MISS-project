# 预设 [+] 按钮改造：弹窗创建角色

> 发现日期：2026-06-26 | 类型：交互重构

---

## 需求

- 移除属性调节面板中的"提示词生成属性"区域（输入框 + ✨ 生成按钮）
- 点击侧边栏预设区的 **[+]** 按钮时，弹出弹窗
- 弹窗内输入角色描述，一键生成属性并创建预设

---

## 当前状态（改前）

```
属性面板
├── 属性滑块 × 10
├── ❌ 提示词输入框 + ✨ 生成按钮   ← 要删掉
└── 人物背景 textarea              ← 保留

侧边栏预设区
└── [+] ⭐ 📂   ← [+] 目前直接 pop 输入名称，无生成功能
```

## 目标状态（改后）

```
属性面板
├── 属性滑块 × 10
└── 人物背景 textarea              ← 保留

侧边栏预设区
└── [+] ⭐ 📂
     ↓ 点击 [+]
   ┌──────────────────┐
   │  ✦ 创建新角色      │
   │                   │
   │  角色名称: [____]  │
   │  角色描述: [____]  │
   │  人物背景: [____]  │  (可选)
   │                   │
   │  [取消]  [✨ 生成并创建] │
   └──────────────────┘
```

---

## 文件变更：`frontend/index.html`

### 1. 删除属性面板中的生成区域（~L362-L373）

移除以下整块 HTML：

```html
<!-- 提示词生成属性 -->
<div class="mt-3">
  <div class="flex gap-1">
    <input id="characterPrompt" type="text" placeholder="描述想要的角色...如：傲娇猫娘，喜欢撒娇但嘴上不承认"
      class="flex-1 px-2 py-1.5 rounded-md outline-none"
      style="border:1px solid var(--color-border);font-size:var(--font-size-xs);background:var(--color-bg);color:var(--color-text);">
    <button onclick="generateFromPrompt()" class="cursor-pointer px-2.5 py-1.5 rounded-md text-white font-medium"
      style="border:none;background:var(--color-primary);font-size:var(--font-size-xs);white-space:nowrap;">
      ✨ 生成
    </button>
  </div>
</div>
```

### 2. 新增弹窗 HTML（放在 settingsModal 之后，`</body>` 之前）

参照 settingsModal 的模式：

```html
<!-- ═══════════════════ 新建预设弹窗 ═══════════════════ -->
<div id="newPresetModal" class="hidden fixed inset-0 z-[2600] flex items-center justify-center" style="background:rgba(0,0,0,0.4);" onclick="if(event.target===this)closeNewPresetModal()">
  <div class="rounded-xl p-5" style="background:var(--color-surface);border:1px solid var(--color-border);box-shadow:var(--shadow-lg);width:420px;max-width:90vw;" onclick="event.stopPropagation()">
    <div class="flex justify-between items-center mb-4">
      <span class="font-semibold" style="font-size:var(--font-size-md);color:var(--color-text);">✦ 创建新角色</span>
      <button onclick="closeNewPresetModal()" class="cursor-pointer" style="border:none;background:none;font-size:18px;color:var(--color-text-muted);line-height:1;">✕</button>
    </div>
    <div class="flex flex-col gap-3">
      <div>
        <label class="block mb-1" style="font-size:var(--font-size-sm);color:var(--color-text-secondary);">角色名称</label>
        <input id="newPresetName" type="text" placeholder="例如：傲娇猫娘" class="w-full px-3 py-2 rounded-md outline-none" style="border:1px solid var(--color-border);font-size:var(--font-size-base);background:var(--color-bg);color:var(--color-text);">
      </div>
      <div>
        <label class="block mb-1" style="font-size:var(--font-size-sm);color:var(--color-text-secondary);">角色描述 <span style="color:var(--color-text-muted);">（AI 根据描述自动分析属性）</span></label>
        <textarea id="newPresetDesc" placeholder="描述角色性格...如：傲娇猫娘，喜欢撒娇但嘴上不承认，好奇心强，对主人特别依赖" rows="3" class="w-full px-3 py-2 rounded-md outline-none" style="border:1px solid var(--color-border);font-size:var(--font-size-base);background:var(--color-bg);color:var(--color-text);resize:vertical;"></textarea>
      </div>
      <div>
        <label class="block mb-1" style="font-size:var(--font-size-sm);color:var(--color-text-secondary);">人物背景 <span style="color:var(--color-text-muted);">（可选）</span></label>
        <textarea id="newPresetBackground" placeholder="写出她的人物背景故事..." rows="2" class="w-full px-3 py-2 rounded-md outline-none" style="border:1px solid var(--color-border);font-size:var(--font-size-base);background:var(--color-bg);color:var(--color-text);resize:vertical;"></textarea>
      </div>
    </div>
    <div class="flex justify-between items-center" style="margin-top:16px;">
      <span id="newPresetStatus" style="font-size:var(--font-size-xs);color:var(--color-text-muted);"></span>
      <div class="flex gap-2">
        <button onclick="closeNewPresetModal()" class="cursor-pointer px-4 py-2 rounded-md" style="border:1px solid var(--color-border);background:var(--color-surface-alt);color:var(--color-text-secondary);font-size:var(--font-size-sm);">取消</button>
        <button id="newPresetBtn" onclick="createPresetFromModal()" class="cursor-pointer px-4 py-2 rounded-md text-white font-medium" style="border:none;background:var(--color-primary);font-size:var(--font-size-sm);">✨ 生成并创建</button>
      </div>
    </div>
  </div>
</div>
```

### 3. 改写 JS 函数

#### 3.1 删除旧的 `generateFromPrompt` 和 `createPreset`

删除 ~L971-L998 的 `generateFromPrompt` 函数。删除 ~L851-L859 的旧 `createPreset` 函数。

#### 3.2 新增函数（放在 JS 末尾 `/* ── 初始化 ── */` 之前）

```javascript
  /* ── 新建预设弹窗 ── */
  window.openNewPresetModal = function(){
    document.getElementById('newPresetModal').classList.remove('hidden');
    document.getElementById('newPresetName').focus();
    document.getElementById('newPresetStatus').textContent = '';
  };
  window.closeNewPresetModal = function(){
    document.getElementById('newPresetModal').classList.add('hidden');
  };
  window.createPresetFromModal = async function(){
    var name = document.getElementById('newPresetName').value.trim();
    var desc = document.getElementById('newPresetDesc').value.trim();
    var bg = document.getElementById('newPresetBackground').value.trim();
    var status = document.getElementById('newPresetStatus');
    var btn = document.getElementById('newPresetBtn');

    if(!name){ toastMsg('请输入角色名称'); return; }
    if(!desc){ toastMsg('请输入角色描述'); return; }

    btn.disabled = true;
    btn.textContent = '⏳ 分析中...';
    status.textContent = '正在分析角色属性...';

    try {
      var resp = await fetch('/api/character/analyze', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({description: desc})
      });
      if(!resp.ok){
        var errData = await resp.json().catch(function(){ return {}; });
        throw new Error(errData.detail || '分析失败');
      }
      var data = await resp.json();
      ATTRS.forEach(function(a){
        if(data.profile[a] !== undefined){
          profile[a] = data.profile[a];
          syncControls(a, data.profile[a]);
        }
      });
      applyProfile();
      status.textContent = '属性分析完成，正在保存...';
    } catch(e) {
      status.textContent = '';
      btn.disabled = false;
      btn.textContent = '✨ 生成并创建';
      toastMsg('生成失败：' + e.message);
      return;
    }

    // 保存预设
    try {
      var saveResp = await fetch('/api/preset/save', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name: name, profile: appliedProfile, background: bg})
      });
      var saveData = await saveResp.json();
      activePresetName = name;
      if(bg){ document.getElementById('characterBackground').value = bg; }
      toastMsg('已创建：' + saveData.name);
      loadPresets();
      closeNewPresetModal();
    } catch(e) {
      toastMsg('属性已生成但保存失败：' + e.message);
    }

    btn.disabled = false;
    btn.textContent = '✨ 生成并创建';
    status.textContent = '';
    document.getElementById('newPresetName').value = '';
    document.getElementById('newPresetDesc').value = '';
    document.getElementById('newPresetBackground').value = '';
  };
```

#### 3.3 创建旧 `createPreset` 的代理

侧边栏 [+] 按钮的 `onclick` 仍为 `createPreset()`，所以需要保留一个指向弹窗的简单代理：

```javascript
  window.createPreset = function(){
    openNewPresetModal();
  };
```

### 4. 已暴露到 window 的函数确认

确保以下函数都挂载到 `window`：

| 函数 | 确保写法 |
|------|---------|
| `createPreset` | `window.createPreset = function(){ ... }` |
| `saveCurrentPreset` | `window.saveCurrentPreset = async function(){ ... }` |
| `importPresetFile` | `window.importPresetFile = function(){ ... }` |
| `openNewPresetModal` | `window.openNewPresetModal = function(){ ... }` |
| `closeNewPresetModal` | `window.closeNewPresetModal = function(){ ... }` |
| `createPresetFromModal` | `window.createPresetFromModal = async function(){ ... }` |

---

## 不涉及后端修改

`POST /api/character/analyze` 端点无需任何修改，前端直接复用。

---

## 验证清单

- [ ] 属性面板不再有"提示词输入框 + ✨ 生成"行
- [ ] 点击侧边栏 [+] 弹出弹窗（不是空的 pop 输入框）
- [ ] 弹窗有三个输入框：角色名称、角色描述、人物背景（可选）
- [ ] 填入名称 + 描述后点"✨ 生成并创建"，弹窗显示进度
- [ ] 成功后属性滑块自动填充、预设保存到数据库、侧边栏刷新
- [ ] 不填名称或描述时 toast 提示
- [ ] 点弹窗外灰色区域关闭弹窗
- [ ] 弹窗内 ✕ 按钮关闭弹窗
- [ ] ⭐ 保存 和 📂 导入 按钮也正常工作
