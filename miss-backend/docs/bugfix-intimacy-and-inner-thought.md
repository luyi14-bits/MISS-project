# 内心独白 + 亲密度 修复文档

> 给接手程序员的技术说明。涉及 3 个问题，按文件给出需修改的位置和建议代码。

---

## 问题 1：只有第一句显示内心独白

### 1.1 根因

三条叠加：

| 根因 | 位置 | 说明 |
|------|------|------|
| 新消息不继承"内心独白"展开状态 | `index.html` ~L790 | `toggleAllInner()` 只操作已有 DOM，新消息的 `.msg-inner` 不加 `expanded` |
| CSS max-height 截断 | `index.html` ~L546 | `.msg-inner.expanded { max-height:120px }` — 长文本被裁 |
| LLM 返回 JSON 不规范时 inner_thought 为空 | `llm_caller.py` ~L260 | `_parse_json_response` 失败后返回 `""`，前端 `if(innerText)` 为 false |

### 1.2 修复方案

**A. 新消息跟随复选框：**

> 文件：`frontend/index.html`，`buildMsgHTML()` 函数附近

在 `buildMsgHTML` 中判断 `showInner` 复选框，初始 class 跟随它：

```javascript
function buildMsgHTML(type, avatarHtml, sender, text, innerText){
    var h='<div class="msg-row '+type+' msg-animate">'+avatarHtml+'<div class="msg-body"><div class="msg-sender">'+escapeHtml(sender)+'</div>';
    if(text){ h+='<div class="msg-bubble"'+(type==='miss'?' onclick="toggleInner(this)"':'')+'>'+escapeHtml(text)+'</div>'; }
    if(innerText){
        var expanded = document.getElementById('showInner').checked ? ' expanded' : '';
        h+='<div class="msg-inner'+expanded+'">'+escapeHtml(innerText)+'</div>';
    }
    h+='</div></div>'; return h;
}
```

**B. CSS max-height 改为 auto：**

> 文件：`frontend/index.html`，CSS 部分

```css
/* 改前 */
.msg-inner.expanded { max-height:120px;margin:4px 4px 0;padding:8px 10px; }
/* 改后 */
.msg-inner.expanded { max-height:none;margin:4px 4px 0;padding:8px 10px; }
```

**C. (可选) prompt 中强调 JSON 格式：**

> 文件：`services/prompt_builder.py`

在 system prompt 末尾加重 JSON 输出要求，减少 LLM 返回非 JSON 的概率。如果 LLM 已经稳定返回 JSON 则跳过这步。

---

## 问题 2：亲密度不增减

### 2.1 根因

**整个代码库没有 intimacy 增减机制。**

- `routers/chat.py` 的响应中无 `intimacy_change` 字段
- `services/attribute_engine.py` 是纯只读（EasterEggEngine、CrossEffectCalculator、KnowledgeFilter 都不改任何属性值）
- 亲密度当前是纯静态输入：用户手动调滑块 → 随 `profile` 参数发给 prompt → 值永不变

### 2.2 修复方案（分三步）

#### 第 1 步：后端增加 intimacy 计算

> 新文件：`services/attribute_engine.py`，追加类

```python
class IntimacyEngine:
    """根据对话内容分析亲密度增减。
    正数词 = +1~3，负数词 = -1~3，每次对话返回一个变化值。"""

    POSITIVE_PATTERNS = [
        (r"(谢谢|感谢|爱|喜欢|❤|😊|贴贴|抱抱|亲亲|陪伴|温暖|开心|懂我)", 2),
        (r"(聊得|说得|好|棒|厉害|聪明|不错|赞)", 1),
    ]
    NEGATIVE_PATTERNS = [
        (r"(讨厌|走开|闭嘴|滚|烦|恶心|无聊|没用|笨|蠢)", -2),
        (r"(不是|不对|没有|算了|再见)", -1),
    ]

    def evaluate(self, user_message: str, current_intimacy: int) -> dict:
        """
        返回 {"change": int, "reason": str}
        change 可为正、负、零。最终 intimacy 范围限制在 0~100。
        """
        score = 0
        reasons = []

        for pattern, value in self.POSITIVE_PATTERNS:
            if re.search(pattern, user_message):
                score += value
                reasons.append(f"+{value}")

        for pattern, value in self.NEGATIVE_PATTERNS:
            if re.search(pattern, user_message):
                score += value
                reasons.append(f"{value}")

        return {"change": score, "reason": ", ".join(reasons) if reasons else "无变化"}
```

#### 第 2 步：chat 路由返回 intimacy_change

> 文件：`routers/chat.py`

在 `chat()` 函数中调用 IntimacyEngine，在响应中增加字段：

```python
# 在 router 定义区
_intimacy_engine = IntimacyEngine()

# 在 @router.post("/chat") 函数末尾 return 前
intimacy_result = _intimacy_engine.evaluate(req.message, req.profile.intimacy)
intimacy_result["intimacy"] = max(0, min(100, req.profile.intimacy + intimacy_result["change"]))

# 在 return 字典中增加
return {
    # ... 原有字段 ...
    "intimacy_change": intimacy_result["change"],
    "intimacy": intimacy_result["intimacy"],
    "intimacy_reason": intimacy_result["reason"],
}
```

#### 第 3 步：前端接收并更新亲密度滑块

> 文件：`frontend/index.html`，`sendMsg()` 的 `.then(function(data){...})` 中

```javascript
.then(function(data){
    // ... 原有渲染代码 ...

    // 更新亲密度
    if(data.intimacy_change !== undefined && data.intimacy_change !== 0){
        var newVal = data.intimacy;
        profile['intimacy'] = newVal;
        appliedProfile['intimacy'] = newVal;
        syncControls('intimacy', newVal);
        if(data.intimacy_change > 0){
            toastMsg('亲密度 +' + data.intimacy_change);
        } else if(data.intimacy_change < 0){
            toastMsg('亲密度 ' + data.intimacy_change);
        }
    }
})
```

### 2.3 亲密度范围

- `MISSProfile` 中 intimacy 字段定义：`ge=0, le=100`
- 计算时用 `max(0, min(100, current + change))` 确保不越界
- 负数词可以让亲密度降到 0（不会到负数）

---

## 附：当前架构快速索引

```
miss-backend/
├── main.py                    # FastAPI app, 注册路由
├── config.py                  # 环境变量 + 运行时覆盖（仅 key/url/model）
├── database.py                # SQLite 初始化
│
├── routers/
│   ├── chat.py                # POST /api/chat, /api/chat/stream
│   ├── preset.py              # 预设 CRUD API
│   ├── admin.py               # 管理 API
│   └── settings.py            # GET/POST /api/settings
│
├── services/
│   ├── llm_caller.py          # AsyncOpenAI 封装, call() + stream()
│   ├── prompt_builder.py      # 构造 system prompt 和消息历史
│   ├── attribute_engine.py    # MISSProfile, EasterEggEngine, KnowledgeFilter
│   ├── memory_manager.py      # ConversationStore（SQLite 消息存储）
│   └── vector_store.py        # ChromaDB 长期记忆
│
├── frontend/
│   └── index.html             # 单文件全栈前端
│
└── tests/                     # 208 个测试，pytest
```

### 关键数据流

```
用户发消息 → sendMsg()
  → POST /api/chat {session_id, message, profile}
    → PromptBuilder.build_full()   → 组装 [system, history..., user]
    → LLMCaller.call(messages)     → AsyncOpenAI API call
    → (新增) IntimacyEngine.evaluate() → intimacy_change
    → 返回 {inner_thought, spoken, intimacy_change, intimacy}
  → 前端渲染消息 + 更新亲密度滑块
```

---

文档日期：2026-06-26
