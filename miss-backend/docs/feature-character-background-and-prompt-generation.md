# 人物背景 + 提示词生成属性 功能文档

> 给接手程序员的技术说明。涉及两个新功能：预设角色背景故事 + 用户用自然语言描述角色自动生成属性。

---

## 功能 1：预设角色背景故事

### 1.1 需求

现有 4 个内置预设（傲娇女友、知性姐姐、笨蛋⑨、冰山美人）只有属性滑块值，没有角色背景。需要给每个角色加上一段背景描述，让 LLM 更好地扮演。

### 1.2 数据结构变更

#### 后端 — Preset 模型

> 文件：`models/preset.py`

在 SQLite 表中增加 `background` 字段：

```python
# 在 Preset 模型类中增加
background = Column(Text, default="")
```

#### 后端 — Preset Schema

> 文件：`routers/preset.py`

在 save/load 的 Pydantic schema 中增加 `background` 字段：

```python
class PresetSaveRequest(BaseModel):
    name: str
    profile: dict
    background: str = ""   # 新增
```

所有 preset CRUD 端点（save、get、list、import、export）都增加对 `background` 的读写。

#### 前端 — 预设卡片 + 编辑区

> 文件：`frontend/index.html`

1. 在预设卡片上点击时，切换到该预设，同时在侧边栏下方显示一段可编辑的背景文本区域
2. 或在属性面板下方加一个"背景故事" textarea

建议布局（属性面板底部）：

```html
<div class="mt-3">
  <label style="font-size:var(--font-size-sm);color:var(--color-text-secondary);">人物背景</label>
  <textarea id="characterBackground" placeholder="写出她的人物背景、性格设定..."
    class="w-full px-3 py-2 rounded-md mt-1" 
    style="border:1px solid var(--color-border);font-size:var(--font-size-base);background:var(--color-bg);color:var(--color-text);resize:vertical;min-height:80px;"
  ></textarea>
</div>
```

保存预设时把 `characterBackground` 的值一起发到后端。

### 1.3 System Prompt 注入

> 文件：`services/prompt_builder.py`

在 `build_full()` 的 system prompt 构造中追加角色背景：

```python
background = ctx.get("character_background", "")
if background:
    system_parts.append(f"【你的人物背景设定】\n{background}")
```

效果：LLM 收到 prompt 时会看到类似：
```
【你的人物背景设定】
你是被宅男程序员在二手显卡里发现的自称AI少女。说话带电子口癖，对硬件特别敏感...
```

人物背景 + 属性滑块值一起作用，LLM 的角色扮演会更立体。

---

## 功能 2：用户写提示词自动生成属性

### 2.1 需求

用户在文本框输入类似 "傲娇猫娘，喜欢撒娇但嘴上不承认，好奇心强" → 后端调 LLM 分析这段文字，返回 10 属性值 → 前端自动填充滑块。

### 2.2 后端 API

> 文件：`routers/chat.py`（或新建 `routers/character.py`）

新增端点 `POST /api/character/analyze`：

```python
class CharacterAnalyzeRequest(BaseModel):
    description: str   # 用户输入的角色描述文本

@router.post("/character/analyze")
async def analyze_character(req: CharacterAnalyzeRequest):
    prompt = f"""你是一个角色属性分析器。根据用户的文字描述，分析角色在以下 10 个维度的属性值。每个值范围是 -100 到 100（整数），其中 intimacy（亲密度）范围是 0 到 100。

属性说明：
- rational_emotional：理性(-100) vs 感性(100)
- willpower：意志力薄弱(-100) vs 意志力坚定(100)
- independent_submissive：独立(-100) vs 顺从(100)
- education_level：低教育(-100) vs 高教育(100)
- intimacy：低亲密(0) vs 高亲密(100)  ← 注意下限 0
- curiosity：低好奇(-100) vs 高好奇(100)
- humor：严肃(-100) vs 幽默(100)
- aggression：温和(-100) vs 攻击性(100)
- social_energy：内向(-100) vs 外向(100)
- adventurousness：保守(-100) vs 冒险(100)

用户描述：{req.description}

只返回一个纯 JSON 对象，格式如下，不要任何额外文字：
{{"rational_emotional": 60, "willpower": 30, ...}}"""

    # 复用现有 LLMCaller，请求一个很小的回复
    messages = [{"role": "user", "content": prompt}]
    result = await _caller.call(messages, model_config={"max_tokens": 200, "temperature": 0.3})

    # 解析 JSON
    # ...
    return parsed_profile
```

**关键点**：这个端点也走用户的 API key（`_caller` 已经读取 `get_api_key()` / `get_base_url()`）。用户自己的 key 自己用，不额外消耗服务端配额。

### 2.3 前端 UI

> 文件：`frontend/index.html`

在属性面板区域上方或预设卡片区域加一个入口：

```html
<div class="mb-3">
  <div class="flex gap-1">
    <input id="characterPrompt" type="text" placeholder="描述你想要的角色，例如：傲娇猫娘，喜欢撒娇但嘴上不承认" 
      class="flex-1 px-3 py-2 rounded-md outline-none" 
      style="border:1px solid var(--color-border);font-size:var(--font-size-sm);background:var(--color-bg);color:var(--color-text);">
    <button onclick="generateFromPrompt()" class="cursor-pointer px-3 py-2 rounded-md text-white font-medium" 
      style="border:none;background:var(--color-primary);font-size:var(--font-size-sm);white-space:nowrap;">
      ✨ 生成
    </button>
  </div>
</div>
```

生成按钮的 JS：

```javascript
window.generateFromPrompt = async function(){
  var desc = document.getElementById('characterPrompt').value.trim();
  if(!desc){ toastMsg('请输入角色描述'); return; }

  toastMsg('正在分析角色...');
  try {
    var resp = await fetch('/api/character/analyze', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({description: desc})
    });
    var data = await resp.json();
    // data = {rational_emotional:60, willpower:30, ...}

    // 填充到 profile 并同步滑块
    ATTRS.forEach(function(a){
      if(data[a] !== undefined){
        profile[a] = data[a];
        syncControls(a, data[a]);
      }
    });
    applyProfile();
    toastMsg('角色属性已生成！');
  } catch(e) {
    toastMsg('生成失败，请检查 API 设置');
  }
};
```

---

## 文件变更清单

| 文件 | 改动 |
|------|------|
| `models/preset.py` | Preset 表加 `background` 字段 |
| `routers/preset.py` | save/load/import/export 增加 background 读写 |
| `routers/chat.py` 或新建 `routers/character.py` | 新增 `POST /api/character/analyze` |
| `services/prompt_builder.py` | system prompt 中注入角色背景 |
| `frontend/index.html` | 背景 textarea + 提示词输入框 + 生成按钮 + JS |
| `main.py` | 注册 character 路由（如单独放） |

---

## 数据流（完整）

```
用户操作                             后端
─────────                           ─────
[属性面板] 输入提示词 → 点✨生成     → POST /api/character/analyze
                                    → LLMCaller.call() 分析文本
                                    → 返回 10 属性值 JSON
← 前端填充滑块 + 应用

[属性面板] 写人物背景 textarea      → 保存预设时一起发
[属性面板] 调滑块                    → applyProfile()

发消息                              → POST /api/chat
                                    → PromptBuilder 注入背景 + 属性
                                    → LLMCaller.call() 生成回复
                                    → (新) IntimacyEngine 计算亲密度
← 渲染 spoken + inner_thought + 更新滑块
```

---

文档日期：2026-06-26
