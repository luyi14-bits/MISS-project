---
name: "Luyi14-coding-ethics"
description: "编程八荣八耻行为准则。强制要求：不瞎猜接口、不模糊执行、不臆想业务、不创造接口、不跳过验证、不破坏架构、不假装理解、不盲目修改。在所有编码任务中均应遵守。Invoke when writing, reviewing, or modifying any code."
---

# 编程八荣八耻

本规范源自大量软件工程实践中的血泪教训。**每一条"耻"背后都有一个真实的 Bug 或线上事故隐患。**

---

## 规范架构全景

```
┌────────────────────────────────────────────────────────────────┐
│                      编程八荣八耻 规范体系                        │
├────────────┬────────────┬────────────┬────────────┬─────────────┤
│  代码组织   │  异常处理   │  配置数据   │  接口契约   │  前端/部署   │
├────────────┼────────────┼────────────┼────────────┼─────────────┤
│ 模块导出    │ 异常全覆盖  │ 配置管理    │ API 降级    │ UI 线程隔离  │
│ 类型声明    │ 日志覆盖    │ 数据库适配  │ 接口契约    │ 资源路径     │
│ 应用生命周期 │            │ 敏感加密    │ 跨语言桥接  │ SW 缓存策略  │
│             │            │            │            │ CDN 降级     │
├────────────┴────────────┴────────────┴────────────┴─────────────┤
│  算法安全专项：余数映射 / 条件分支 / 类型混用 / 状态机恢复       │
├────────────────────────────────────────────────────────────────┤
│  自测循环专项：多策略验证 / 结果自验 / 自动降级 / CLI 自测脚本   │
├────────────────────────────────────────────────────────────────┤
│  安全红线：19 条零容忍条目                                       │
├────────────────────────────────────────────────────────────────┤
│  快速自检：24 条提交前必问                                       │
└────────────────────────────────────────────────────────────────┘
```

## 规范演进史

| 阶段 | 来源项目 | 新增条目 | 核心教训 |
|------|---------|---------|---------|
| V1 基础版 | MISS / 通用 | 14 条荣耻 + 11 条红线 | Python/C# 双语言混合项目的安全基线 |
| V2 算法安全 | 天问 (25 Bug) | 第十五~十七荣耻 + 算法专项 | 余数映射 / 类型返回 / 跨模式渲染 |
| V3 前端/部署 | 阴阳先生 (13 Bug) | 第十八~二十荣耻 + 6 条新红线 | 导航过滤 / CDN 降级 / SW 缓存策略 |
| V4 风格注入 | WeChatAuto / TravelFace / 微博情感 | 架构全景图 + 演进史 | 架构先行 / 核心问题→方案→模块 三段式 |
| V5 自测循环 | WeChatAuto (SmartSendExecutor) | 第二十一荣耻 + 自测专项 | 多策略验证 / 结果自验 / CLI 自测脚本 |

---

## 第一荣：模块导出清晰完整
## 第一耻：写完类不导出，留着过年

**后果**：外部 `from services import SomeClass` → `ImportError`，调用方只能绕开 `__init__.py` 直接导入，架构退化。

**典型场景**：
- 新增的公开类/函数未在 `__init__.py` 注册
- 多个模块各自独立定义 ORM Base

**正确做法**：
```python
# services/__init__.py — 每一个公开类/函数都必须在此注册
from .engine import Engine, Parser, Calculator
__all__ = ["Engine", "Parser", "Calculator"]
```

> **规则**：每新增一个模块公开类/函数，**同步**在 `__init__.py` 中添加导出。

---

## 第二荣：异常处理全覆盖
## 第二耻：异常直抛不降级，commit 失败不回滚

**后果**：`db.commit()` 抛异常 → 事务不回滚 → 数据库不一致 → 后续操作雪崩。

**典型场景**：数据操作只有 `finally: db.close()`，无 `rollback`。

**正确做法**（铁律模板）：
```python
def db_operation():
    db = SessionLocal()
    try:
        db.commit()
    except Exception:
        db.rollback()       # ← 必须！
        raise               # ← 向上传播
    finally:
        db.close()          # ← 必须！
```

**降级模板**（对外服务接口）：
```python
def service_method():
    try:
        return store.get_data(key)
    except OperationalError:
        return default_value  # ← 降级继续服务
```

> **规则**：所有数据库操作必须有 `rollback`。所有对外接口必须有降级路径。

---

## 第三荣：配置管理用最佳实践
## 第三耻：轮子不用原生，手动重复造

**后果**：手写 `load_dotenv()` + `os.getenv()` 与框架的 `BaseSettings` 功能重叠，配置读取时机不可控。

**错误 vs 正确**：
```python
# ❌ 冗余
load_dotenv()
class Settings(BaseSettings):
    api_key: str = os.getenv("API_KEY", "")

# ✅ 版本
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    api_key: str = ""
```

---

## 第四荣：数据库操作可移植
## 第四耻：数据库专有参数硬编码

```python
# ❌ 硬编码 SQLite 参数
engine = create_engine(url, connect_args={"check_same_thread": False})

# ✅ 根据 db_url 动态决定
extra = {}
if "sqlite" in config.db_url:
    extra["connect_args"] = {"check_same_thread": False}
engine = create_engine(config.db_url, **extra)
```

---

## 第五荣：类型声明完整清晰
## 第五耻：字典满天飞，TypedDict 不用

**规则**：返回值是 dict 且结构固定 → 必须定义 TypedDict。Pydantic Field 必须加 `description`。

---

## 第六荣：应用生命周期规范
## 第六耻：模块导入时执行副作用

**规则**：`init_db()` 等副作用必须放在 `lifespan` 中，禁止模块级执行。

---

## 第七荣：测试即文档
## 第七耻：写完代码不补测试，旧测试不同步

---

## 第八荣：API 调用走封装层
## 第八耻：绕过封装层直接调 SDK

---

## 第九荣：日志全面覆盖
## 第九耻：except 静默吞异常，线上问题查不到

### 核心问题

线上用户反馈"点发送没反应"，开发者打开日志——空的。`except Exception: pass` 把异常全吞了。

### 最终方案

```python
# ❌ 静默吞异常 → 线上故障无法追踪
except Exception:
    pass

# ✅ 每条 except 都必须写日志
except Exception as e:
    logging.warning(f"[降级] 操作失败: {e}")
```

### 设计要点
- 零容忍 `except Exception: pass`
- 用 `logging.warning` 而非 `print`（可路由到文件/ELK）
- 日志信息必须包含上下文（哪个模块、哪种操作）

---

## 第十荣：API 调用多级降级
## 第十耻：死绑一种 API 模式，兼容性为零

**后果**：死绑单一 API 模式 → 不同协议/中转站/代理全部失败。

**正确做法**（三级 fallback 架构）：
```python
# Level 1: 标准模式
try:
    resp = await client.call(mode="standard", ...)
    return resp
except Exception as e:
    logging.warning(f"Level 1 failed: {e}, falling back...")

# Level 2: 降级模式
try:
    resp = await client.call(mode="fallback", ...)
    return resp
except Exception as e:
    logging.warning(f"Level 2 failed: {e}, falling back...")

# Level 3: 裸调用
try:
    resp = await client.call(mode="bare", ...)
    return resp
except json.JSONDecodeError:
    return {"error": True, "message": "响应异常，请重试"}
```

> **规则**：所有外部 API 调用必须有降级路径。

---

## 第十一荣：并发 + 异步安全
## 第十一耻：UI 线程做 IO，死锁等重启

**后果**：UI 线程直接读写文件 → 界面冻结数秒 → 用户以为崩溃。

**正确做法**：
```csharp
// ❌ 同步 IO 卡 UI
var text = File.ReadAllText(path);

// ✅ Task.Run 隔离
var text = await Task.Run(() => File.ReadAllText(path));
```

> **规则**：UI 线程禁止直接 IO/网络操作。

---

## 第十二荣：资源路径正确引用
## 第十二耻：硬编码路径导致发布后崩溃

**后果**：开发环境中的相对路径/绝对路径在打包发布后可能全部失效。

**正确做法**：
```csharp
// ❌ 硬编码路径
<Image Source="/Resources/Images/logo.jpg"/>

// ✅ 文件系统路径 + 存在性检查
public static string ResolvePath(string name)
{
    var baseDir = AppDomain.CurrentDomain.BaseDirectory;
    var path = Path.Combine(baseDir, "Resources", name);
    return File.Exists(path) ? path : fallbackPath;
}
```

> **规则**：所有资源必须用文件系统路径 + `File.Exists()` 检查。

---

## 第十三荣：多语言互调桥接
## 第十三耻：多线程同时持全局锁，死锁崩全局

**后果**：多个线程同时调用另一语言的运行时 → 锁竞争 → 循环等待 → 全局冻结。

**正确做法**：单一工作线程串行化所有跨语言调用，`TaskCompletionSource` 桥接异步等待。

> **规则**：跨语言调用必须走单一线程串行化队列。

---

## 第十四荣：敏感数据加密
## 第十四耻：明文落盘，密钥泄露

**后果**：API Key / Token / 密钥明文存储在配置或数据库中 → 任何有文件读取权限的进程可窃取。

**正确做法**：敏感字段必须先加密再持久化，加解密走统一的加密服务。

> **规则**：API Key / Token / 密钥等敏感信息禁止明文存储。

---

## 第十五荣：接口契约即法律
## 第十五耻：假设返回值类型，不看文档不验证

**后果**：函数 `hourToShift(hour)` JSDoc 标注返回 `number`，调用者却写 `shift.zhiNum`（当对象解构）→ `undefined` → 连锁崩溃。

**实战案例**（天问 B5，最严重运行时崩溃）：
```javascript
// ❌ 错误：假设返回值是对象
var shift = LunarCalendar.hourToShift(hour);
var hourZhi = shift.zhiNum;  // shift 是 number(12)，没有 .zhiNum，→ undefined

// ✅ 正确：按 JSDoc 使用返回值
// JSDoc: @returns {number} 1=子时...12=亥时
var hourZhi = LunarCalendar.hourToShift(hour);
```

**根因**：函数 `@returns` 标签与实际返回值不一致。调用者凭感觉使用，不验证。

> **规则**：调用函数前必须读 JSDoc/type hint。返回值类型不确定时，`console.log(typeof result)` 验证后再用。零容忍"猜类型"。

---

## 第十六荣：状态机全量恢复
## 第十六耻：模式切换只做一半，持久化后读不回

**后果**：7 种模式 + 子模式 → `switchMode()` 遗漏恢复逻辑 → 切换标签后结果丢失/UI 卡死。

**实战案例**（天问：B2/D3/A2/B7 — 同模式 Bug 重复 4 次）：
```javascript
// ❌ 错误：switchMode('liuren') 不恢复子模式 UI
function switchMode(mode) {
    // ... 
    if (mode === 'liuren') {
        controls.classList.remove('hidden');
        // 漏了 switchLiurenSubMode(currentLiurenSubMode) → tab 状态不一致
    }
}

// ✅ 正确：切换时恢复全部子状态
function switchMode(mode) {
    // ...
    if (mode === 'liuren') {
        controls.classList.remove('hidden');
        switchLiurenSubMode(currentLiurenSubMode);  // ← 必须恢复子模式
        if (savedLiurenResult) renderLiurenResult(savedLiurenResult);  // ← 恢复持久化结果
    }
}
```

> **规则**：状态机切换时必须验证全部子状态恢复（控件显隐 + 数据填充 + UI 状态）。建立统一的 `switchMode + restoreResult` 模板，减少重复代码。

---

## 第十七荣：跨域调用先校验
## 第十七耻：渲染函数无条件复用，数据字段不存在照样传

**后果**：`renderMeihuaResult` 无条件调用 `renderWuge(result)` → 梅花结果无 `strokes` 字段 → `calcWuge` 抛出 TypeError → 整个解释区白屏。

**实战案例**（天问 B8）：
```javascript
// ❌ 错误：不检查数据字段是否存在
function renderMeihuaResult(result, fragment) {
    // ...
    renderWuge(result, fragment);  // result 没有 strokes → calcWuge 崩溃
}

// ✅ 正确：先检查数据字段
function renderMeihuaResult(result, fragment) {
    // ...
    if (result.strokes) {  // ← 守卫：梅花易数没有笔画数据
        renderWuge(result, fragment);
    }
}
```

> **规则**：跨模块复用渲染/计算函数前，必须校验被调用函数所需的数据字段是否存在。不要让"调用方知道被调用方需要什么"成为隐式契约。

---

## 第十八荣：导航逻辑绑定过滤态
## 第十八耻：全局索引导航 + 分类筛选 = 按钮假死

**后果**：分类筛选后 prev/next 按钮在全局数组 `allStories` 中导航 → 分类不匹配时静默 return → 用户点击无效，看起来像程序卡死。

**实战案例**（阴阳先生 第二轮 Bug 3/5）：
```javascript
// ❌ 错误：在全局数组导航
function navigateNext() {
    let idx = allStories.findIndex(s => s.id === currentStoryId);
    let next = allStories[idx + 1];  // 下一个可能是其他分类的
    if (next.category !== currentCategory) return;  // 静默放弃 → 按钮假死
}

// ✅ 正确：在过滤池中导航
function navigateNext() {
    let pool = getFilteredPool();  // 当前分类下的故事列表
    let idx = pool.findIndex(s => s.id === currentStoryId);
    if (idx >= pool.length - 1) { disableNextBtn(); return; }
    let next = pool[idx + 1];
    openStory(next.id);
}
```

> **规则**：任何带筛选/搜索的列表，其导航（prev/next/random）必须在过滤后的数据池中操作。边界处（首尾）必须禁用按钮或循环回绕，禁止静默放弃。

---

## 第十九荣：外部资源有降级
## 第十九耻：CDN/外部字体无 fallback，某地区用户页面抖

**后果**：Google Fonts CDN 在中国大陆不可用 → 字体加载永久阻塞 → FOUT（无样式文字闪烁）+ 布局抖动。

**实战案例**（阴阳先生 第二轮 Bug 8）：
```javascript
// ❌ 错误：无条件依赖外部 CDN
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC&display=swap" rel="stylesheet">

// ✅ 正确：超时检测 + 系统字体降级
// CSS 预设 fallback
body { font-family: 'Noto Serif SC', SimSun, KaiTi, serif; }

// JS 3 秒超时降级
const timeout = setTimeout(() => {
    document.documentElement.classList.add('fonts-failed');  // 切换到系统字体
}, 3000);
document.fonts.ready.then(() => clearTimeout(timeout));
```

> **规则**：所有外部资源（CDN 字体/脚本/样式）必须预设系统级 fallback。网络资源加载必须有超时检测。

---

## 第二十荣：SW 缓存策略分级
## 第二十耻：HTML 用 Cache-First，修复永远不生效

**后果**：Service Worker 对 HTML 文件使用 `Cache-First` → 用户浏览器永久缓存旧版本 → 线上 bug 修复后用户端不更新。

**实战案例**（阴阳先生 第一轮 Bug 2）：
```javascript
// ❌ 错误：HTML 用 Cache-First
self.addEventListener('fetch', event => {
    event.respondWith(caches.match(event.request) || fetch(event.request));
});

// ✅ 正确：分级策略
self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);
    if (isStaticAsset(url.pathname)) {
        // 静态资源：Cache-First（更新通过缓存版本号控制）
        event.respondWith(caches.match(event.request) || fetchAndCache(event.request));
    } else {
        // HTML / API：Network-First
        event.respondWith(networkFirst(event.request));
    }
});
```

> **规则**：HTML 文件必须用 Network-First 策略。SW 每次更新必须提升缓存版本号（v1→v2→v3）。静态资源的 Cache-First 配合版本号管理。

---

## 第二十一荣：自测循环多策略验证
## 第二十一耻：策略执行后不验证，"成功"全靠猜

**后果**：多策略发送系统执行策略1后直接返回"成功" → 实际目标窗口未打开 → 后续发送到错误的聊天 → 用户看到消息发错人了。

**核心问题**：

过去多轮反复修改 `execute_send_flow`，每次都靠用户反馈才知道是否成功。新版微信 UIA 控件行为极不稳定，没有一种策略能在所有场景下可靠工作。需要程序自主测试发送，检测结果，失败后切换策略重试。

**最终方案**（WeChatAuto SmartSendExecutor 实战）：

```python
# ❌ 错误：策略执行后不验证，直接返回成功
def execute(target_name, text_msg, file_path):
    try_strategy_1(target_name)
    send_msg(text_msg)  # 如果策略1没打开窗口，消息发到错误的地方
    return True  # "成功"全靠猜

# ✅ 正确：每策略执行后验证，失败自动降级
class SmartSendExecutor:
    STRATEGIES = [_s1_sidebar, _s2_ctrl_f_esc, _s3_ctrl_f_down]

    def execute(self, target_name, text_msg, file_path):
        errors = []
        for i, strategy in enumerate(self.STRATEGIES):
            try:
                strategy(self.wechat_win, target_name)
                if self._verify_chat_opened(target_name):
                    # 验证通过才发送
                    self._send(text_msg, file_path)
                    if self._verify_message_sent(text_msg):
                        return True
                    errors.append(f"策略{i+1}: 窗口打开但发送验证失败")
                else:
                    errors.append(f"策略{i+1}: 窗口未打开")
            except Exception as e:
                errors.append(f"策略{i+1}: {e}")
        # 全部策略失败 → 抛出包含所有错误信息的异常
        raise Exception("所有策略失败:\n" + "\n".join(errors))
```

### 设计要点
- **每策略必验证**：执行后检查目标状态（如"输入"框是否可见），不验证不算完成
- **结果双重验证**：① 操作前提验证（窗口是否打开）② 操作结果验证（消息是否出现）
- **错误信息聚合**：所有策略的错误信息都收集，最终异常包含完整诊断
- **CLI 自测脚本**：提供独立可运行的 `auto_test.py`，命令行直接测试，不依赖 GUI

> **规则**：多策略系统的每个策略执行后必须有结果验证。全部策略失败时必须抛出包含所有策略错误信息的异常。提供独立 CLI 自测脚本，不依赖人工反馈。

---

## 安全红线（不可协商）

以下行为 **零容忍**，发现即打回：

| # | 红线 |
|---|------|
| 1 | 打包时 `console=True` → 密钥明文暴露在控制台 |
| 2 | CSP 包含 `unsafe-inline` |
| 3 | 硬编码 session_id / user_id |
| 4 | API key / Token 明文存储 |
| 5 | 前端 `onclick="xxx()"` HTML 内联事件 |
| 6 | 绕过认证中间件的公开路径过多 |
| 7 | 解析失败后原文当输出 → 系统提示词泄漏 |
| 8 | `except Exception: pass` 静默吞异常 |
| 9 | 硬编码资源路径 → 打包后异常 |
| 10 | UI 线程直接操作数据库/文件 |
| 11 | 多线程同时持全局锁 |
| 12 | 调用函数不看 JSDoc/type hint → 猜类型 |
| 13 | 模式切换不恢复子状态（控件显隐/数据填充/UI状态） |
| 14 | 跨函数复用不检查数据字段存在性 |
| 15 | 带筛选的列表用全局索引导航 → 按钮假死 |
| 16 | 外部 CDN 无超时降级 → 某地区用户白屏 |
| 17 | HTML 文件用 Cache-First → 修复永不生效 |
| 18 | 多策略系统无结果验证 → 策略"成功"但实际失败 |
| 19 | 自测逻辑用 `except Exception: pass` 吞掉验证失败 |

---

## 算法安全（新增专项）

以下模式极易产生 Bug，必须警惕：

| # | 反模式 | 正确做法 | 实例 |
|---|--------|----------|------|
| 1 | **算法三明治**：`yz === 0 ? 12 : yz` | `(value + offset - 1) % N + 1` | 天问 A1：子年地支算成亥 |
| 2 | **冗余条件分支**：inbox 条件重复两次 | 每个分支独立不重叠 | 阴阳先生 visibleEmails() |
| 3 | **类型混用**：number 当 object 解构 | 读 JSDoc，typeof 验证 | 天问 B5：hourToShift |
| 4 | **余数映射**：`value % N` 返回 0 时的边界处理 | 用统一的余数→序数映射公式 | 天问 A1 |

---

## 打包发布检查清单

打包前必须逐项验证：
- [ ] `console=False`
- [ ] `excludes` 列表中无依赖链所需的包
- [ ] 所有动态 import 的包都有 `hiddenimports`
- [ ] 入口文件末尾有正确的入口调用
- [ ] 打包后在不安装运行时环境的机器上双击验证启动
- [ ] 资源文件已配置到打包清单

---

## Git 提交规范

使用 Conventional Commits：

```bash
# 格式
<type>(<scope>): <description>

# 类型
feat     — 新功能
fix      — Bug 修复
refactor — 重构
chore    — 杂项
docs     — 文档
test     — 测试
```

**最佳实践**：
- 描述用现在时祈使语气
- 正文引用 issue/PR
- 一个 commit 一个逻辑变更

---

## 快速自检表

提交代码前逐项自问：

1. 新增了公开类/函数？ → 去 `__init__.py` 加导出了吗？
2. 写了数据库操作？ → 有 `rollback` 和 `finally: close()` 吗？
3. 写了新模块？ → 有对应的测试吗？
4. 改了现有 API？ → 旧测试同步更新了吗？
5. 调了第三方 SDK？ → 走的是封装层还是原生调用？
6. 用了数据库专有参数？ → 有多数据库适配吗？
7. 返回值是 dict？ → 定义 TypedDict 了吗？
8. Pydantic Field？ → 加了 `description` 吗？
9. 有副作用操作？ → 在 `lifespan` 里还是模块级？
10. 涉及密钥/会话？ → 有没有硬编码、console 打印、明文存储？
11. 写了 except？ → 加日志了吗？绝不允许 `except: pass`
12. 调了外部 API？ → 有降级路径吗？
13. UI 项目？ → 用了 `Task.Run` 隔离 IO 吗？
14. 资源引用？ → 用的是文件系统路径吗？
15. 跨语言调用？ → 走单线程队列了吗？
16. 存敏感数据？ → 加密了吗？
17. 调用了返回值不确定的函数？ → 读 JSDoc/type hint 了吗？验证过 typeof 吗？
18. 新增了模式/标签/视图切换？ → `switchMode` 恢复了全部子状态吗？
19. 跨模块复用了渲染/计算函数？ → 检查过被调方需要的字段都存在了吗？
20. 列表有筛选/搜索？ → 导航在过滤池中操作吗？边界按钮禁用了吗？
21. 用了外部 CDN？ → 有超时检测 + 系统 fallback 吗？
22. 写了 SW？ → HTML 用 Network-First 了吗？缓存版本号升了吗？
23. 写了多策略系统？ → 每个策略执行后有结果验证吗？全部失败有兜底吗？
24. 有自测脚本？ → 验证失败时是 `pass` 吞掉还是 `logging.warning` + 降级？

---

## 通用规则（所有 Skill 必须遵守）

1. **任务闭环**：完成任务后必须在 TodoWrite 中将对应任务标记为 ✅ completed，并同步更新管线看板状态。
2. **禁止越权**：严禁逾越自身角色边界。你是编码规范审查者，负责代码质量和安全检查，不进行架构决策或产品定义。超出专业范围的问题应建议切换到对应 Skill。
3. **留痕问责**：在本 Skill 领域内执行了任何任务（新增规则/修改规范/补充示例/执行安全审查等），必须在同目录 `LOG.md` 中追加条目。格式见 Luyi14-project-secretary §4.5。无日志 = 无追溯 = 打回。
