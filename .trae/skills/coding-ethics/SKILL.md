---
name: "coding-ethics"
description: "编程八荣八耻行为准则。强制要求：不瞎猜接口、不模糊执行、不臆想业务、不创造接口、不跳过验证、不破坏架构、不假装理解、不盲目修改。在所有编码任务中均应遵守。Invoke when writing, reviewing, or modifying any code."
---

# 编程八荣八耻

本规范源自 MISS 项目 40 个验收问题的血泪教训。**每一条"耻"背后都有一个真实的 Bug 或线上事故隐患。**

---

## 第一荣：模块导出清晰完整
## 第一耻：写完类不导出，留着过年

**后果**：外部 `from services import EasterEggEngine` → `ImportError`，调用方只能绕开 `__init__.py` 直接 `from services.attribute_engine import ...`，架构退化。

**MISS 项目实例**（4 次犯过）：
- `EasterEggEngine` 未在 `services/__init__.py` 导出
- `CrossEffectCalculator` 未导出
- `AttributePromptMapper` 未导出
- models 三文件各自独立定义 `Base = declarative_base()`

**正确做法**：
```python
# services/__init__.py — 每一个公开类/函数都必须在此注册
from .attribute_engine import (
    MISSProfile, EasterEggEngine, CrossEffectCalculator, AttributePromptMapper
)
# ... 其他导出
__all__ = [
    "MISSProfile", "EasterEggEngine", "CrossEffectCalculator",
    "AttributePromptMapper", "PromptBuilder", "ConversationStore",
    "MemoryScorer", "MemorySummarizer", "VectorMemoryStore",
]
```

> **规则**：每新增一个模块公开类/函数，**同步**在 `__init__.py` 中添加导出。

---

## 第二荣：异常处理全覆盖
## 第二耻：异常直抛不降级，commit 失败不回滚

**后果**：`db.commit()` 抛异常 → 事务不回滚 → 数据库处于不一致状态 → 后续所有操作雪崩。

**MISS 项目实例**（6 次犯过）：
- `ConversationStore.add_message()` — 只有 `finally: db.close()`，无 `rollback`
- `routers/preset.py` — `save_preset` / `delete_preset` / `import_preset` 三方法全缺 rollback
- `desktop-polish` 发现 4 处 `except Exception: pass` 静默吞掉降级异常

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
        return store.get_window(session_id, limit=N)
    except OperationalError:
        return []           # ← 降级：无历史窗口，继续服务
```

> **规则**：所有数据库操作必须有 `rollback`。所有对外接口必须有降级路径。

---

## 第三荣：配置管理用最佳实践
## 第三耻：轮子不用原生，手动重复造

**后果**：`load_dotenv()` + `os.getenv()` 与 `BaseSettings` 功能重叠 → 配置读取时机不可控。

**MISS 项目实例**：
```python
# ❌ 冗余写法
load_dotenv()
class Settings(BaseSettings):
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

# ✅ 正确写法
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    openai_api_key: str = ""
```

---

## 第四荣：数据库操作可移植
## 第四耻：SQLite 专有参数硬编码

**MISS 项目实例**：
```python
# ❌ 硬编码
engine = create_engine(config.db_url, connect_args={"check_same_thread": False})

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

## 第九荣（新增）：日志全面覆盖
## 第九耻：except 静默吞异常，线上问题查不到

**后果**：`except Exception: pass` → 数据库异常、向量库降级失败、API 超时**全部静默** → 用户只能看到"抱歉"，无任何线索排查。

**MISS 项目实例**：`desktop-polish` 发现 4 处 `except Exception: pass` — `prompt_builder.py`、`memory_summarizer.py`、`vector_store.py`、`main.py`。用户反馈"无法回复"时，日志空空如也。

**正确做法**：
```python
# ❌ 静默吞异常
except Exception:
    pass

# ✅ 每条 except 都必须写日志
except Exception as e:
    logging.warning(f"[降级] XXX 失败: {e}")
    # 如果降级不影响功能，用 warning；如果需要人工关注，用 error
```

> **规则**：项目中**零容忍** `except Exception: pass`。每处 except 必须有 `logging.warning` 或 `logging.error`。

---

## 第十荣（新增）：LLM API 调用多级降级
## 第十耻：死绑一种 API 模式，全网兼容性为零

**后果**：instructor `Mode.TOOLS` 死绑 OpenAI 官方 API → 中转站/Claude proxy/非标准 API 全部返回 400 → 用户只看到"抱歉"。

**MISS 项目实例**：用户反馈 API 测试成功但发消息永远返回"抱歉"，根因是中转站不支持 `tool_choice`。参照 SillyTavern 做法修复为三级 fallback。

**正确做法**（三级 fallback 架构）：
```python
# call() — 三级 fallback，每条路径独立
# Level 1: instructor (TOOLS or JSON, for OpenAI official APIs)
try:
    resp = await self._client.chat.completions.create(..., response_model=ChatResponse, max_retries=2)
    return resp.model_dump()
except Exception as e:
    logging.warning(f"[LLM] Level 1 failed ({type(e).__name__}: {e}), falling back...")

# Level 2: bare AsyncOpenAI + response_format={"type":"json_object"}
try:
    l2_client = AsyncOpenAI(api_key=key, base_url=base)
    l2_resp = await l2_client.chat.completions.create(..., response_format={"type": "json_object"})
    parsed = json.loads(l2_resp.choices[0].message.content)
    return {"inner_thought": ..., "spoken": ...}
except Exception as e:
    logging.warning(f"[LLM] Level 2 failed ({type(e).__name__}: {e}), falling back...")

# Level 3: bare API (ST style) — no instructor, no response_format
try:
    l3_resp = await l3_client.chat.completions.create(...)
    content = l3_resp.choices[0].message.content
    # SEC: json.loads 失败时不返回原文（可能含 system prompt 泄漏）
    parsed = json.loads(content)
    return ...
except json.JSONDecodeError:
    # 安全占位符，非原文
    return {"spoken": "响应格式异常，请重试", "_error": True}
```

> **规则**：所有 LLM API 调用必须有三条降级路径。禁止死绑 `Mode.TOOLS`。

---

## 第十一荣（新增）：并发 + 异步安全
## 第十一耻：UI 线程做 IO，死锁等重启

**后果**：`File.ReadAllText` 在 UI 线程执行 → 界面冻结数秒 → 用户以为崩溃 → 强关进程。

**MISS 项目实例**：`desktop-polish` 发现导出/导入在 UI 线程做 IO。

**正确做法**：
```csharp
// ❌ 同步 IO 卡 UI
var text = File.ReadAllText(path);
File.WriteAllText(path, json);

// ✅ Task.Run 隔离
var text = await Task.Run(() => File.ReadAllText(path));
await Task.Run(() => File.WriteAllText(path, json));
```

```python
# Python 异步用法 — WPF pythonnet 不能调 async
# 用 queue.Queue(maxsize=100) + threading.Event 搞断
# 见 desktop_bridge.py 中的流式熔断模式
```

> **规则**：.NET WPF 中 IO/网络操作必须用 `Task.Run`。禁止 UI 线程直接 `File.ReadAllText` / `File.WriteAllText`。

---

## 安全红线（不可协商）

以下行为 **零容忍**，发现即打回：

| # | 红线 | MISS 实例 |
|---|------|-----------|
| 1 | PyInstaller `console=True` → 用户 API key 明文暴露在控制台 | SEC-001 🔴 |
| 2 | CSP 包含 `unsafe-inline` | SEC-002 🟡 |
| 3 | `session_id: 'default'` 硬编码 → 所有用户共享同一会话 | R-6 🔵 |
| 4 | API key 明文存储（`localStorage` → 改为 `sessionStorage`） | desktop-packaging v2 |
| 5 | 前端 `onclick="xxx()"` HTML 内联属性 → CSP 必须 `unsafe-inline` | desktop-packaging v1 |
| 6 | 绕过 `AuthMiddleware` 的公开路径过多 | AuthMiddleware |
| 7 | `json.loads` 失败后 LLM 原文当 spoken → system prompt 泄漏 | fix-llm-api-compat 🔴 |
| 8 | `except Exception: pass` 静默吞异常，线上问题无法排查 | desktop-polish 🟡 |

---

## 打包发布检查清单

PyInstaller / Tauri 打包前必须逐项验证：

- [ ] `console=False`（一行之差泄露密钥）
- [ ] `excludes` 列表中无任何依赖链所需的包（numpy 被排除导致 chromadb 崩溃）
- [ ] 所有动态 import 的包都有 `hiddenimports`（chromadb 129 子模块缺一不可）
- [ ] 入口文件末尾有 `if __name__ == "__main__": uvicorn.run(...)`
- [ ] `collect_all('chromadb')` 调用，无遗漏的 data files
- [ ] 打包后在不安装 Python 的机器上双击验证启动
- [ ] `tauri.conf.json` `resources` 配置了打包的后端 exe

---

## Git 提交规范（新增）

MISS 项目使用 Conventional Commits：

```bash
# 格式
<type>(<scope>): <description>

# 类型
feat     — 新功能（feat: add 三级 LLM fallback）
fix      — Bug 修复（fix: llm_caller 400 回落 Level 2）
refactor — 重构（refactor: call() 简化 4 方法→1 链）
chore    — 杂项（chore: add gitignore publish/）
docs     — 文档（docs: update README 结构树）
test     — 测试（test: add Level 3 fallback test case）
```

**最佳实践**：
- 描述用现在时祈使语气："add" 不是 "added"
- 正文引用 issue/PR：`Closes #123`
- 一个 commit 一个逻辑变更，不混改无关文件

---

## 快速自检表（v2 — 新增 3 条）

提交代码前，逐项自问：

1. 新增了公开类/函数？ → 去 `__init__.py` 加导出了吗？
2. 写了数据库操作？ → 有 `rollback` 和 `finally: close()` 吗？
3. 写了新模块？ → 有对应的 `tests/test_xxx.py` 吗？
4. 改了现有 API？ → 旧测试同步更新了吗？
5. 调了第三方 SDK？ → 走的是项目封装层还是原生调用？
6. 用了数据库专有参数？ → 有多数据库适配吗？
7. 返回值是 dict？ → 定义 TypedDict 了吗？
8. Pydantic Field？ → 加了 `description` 吗？
9. 有副作用操作？ → 在 `lifespan` 里还是模块级？
10. 涉及密钥/会话？ → 有没有硬编码、console 打印、明文 localStorage？
11. **▸ 新：写了 except？ → 加 logging 了吗？绝不允许 `except: pass`** ← 新增
12. **▸ 新：调了 LLM API？ → 有三条 fallback 路径吗？** ← 新增
13. **▸ 新：C# 项目？ → IO/网络操作用 `Task.Run` 了吗？** ← 新增
