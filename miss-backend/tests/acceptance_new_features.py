# Copyright (C) 2026  MISS Project Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
"""
新功能专项验收测试 - runtime settings + IntimacyEngine + KnowledgeFilter + 10交叉效果
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["DB_URL"] = "sqlite:///./tests/data/test_new_features.db"

from fastapi.testclient import TestClient
from models import Base
from database import engine


def P(t): print(f"  ✅ PASS: {t}")
def F(t, d=""): print(f"  ❌ FAIL: {t}"); d and print(f"     {d}")


def run():
    p = f = 0
    Base.metadata.create_all(bind=engine)

    try:
        from main import app
        client = TestClient(app)
        print("=" * 65)
        print("新功能验收测试 — 2026-06-26 变更集")
        print("=" * 65)

        # ===== 1. /api/settings GET/POST =====
        print("\n── /api/settings 运行时配置 ──")
        r = client.post("/api/settings", json={
            "openai_api_key": "sk-test123", "openai_base_url": "https://test.example.com/v1", "model": "gpt-4o-mini"
        })
        if r.status_code == 200: P("/api/settings POST → 200"); p += 1
        else: F(f"状态码={r.status_code}"); f += 1
        if r.json().get("message") == "设置已保存": P("POST message=设置已保存"); p += 1
        else: F(f"message={r.json().get('message')}"); f += 1

        r2 = client.get("/api/settings")
        if r2.status_code == 200: P("/api/settings GET → 200"); p += 1
        else: F(f"状态码={r2.status_code}"); f += 1
        data = r2.json()
        if data.get("openai_api_key_set"): P("GET: openai_api_key_set=true"); p += 1
        else: F(f"openai_api_key_set={data.get('openai_api_key_set')}"); f += 1
        if data.get("openai_base_url") == "https://test.example.com/v1": P("GET: base_url正确"); p += 1
        else: F(f"base_url={data.get('openai_base_url')}"); f += 1
        if data.get("model") == "gpt-4o-mini": P("GET: model正确"); p += 1
        else: F(f"model={data.get('model')}"); f += 1
        # api_key should be masked
        if "***" in data.get("openai_api_key", ""): P("GET: api_key 脱敏显示"); p += 1
        else: F(f"api_key={data.get('openai_api_key')}"); f += 1

        # ===== 2. IntimacyEngine 正面词汇 =====
        print("\n── IntimacyEngine 亲密度评估 ──")
        from services.attribute_engine import IntimacyEngine
        ie = IntimacyEngine()
        r = ie.evaluate("谢谢你的陪伴，你真懂我！❤️", 50)
        if r["change"] > 0: P(f"正面词 → +{r['change']}"); p += 1
        else: F(f"change={r['change']}"); f += 1
        if "reason" in r: P("含 reason 字段"); p += 1
        else: F("缺 reason"); f += 1

        r2 = ie.evaluate("走开，你好烦", 50)
        if r2["change"] < 0: P(f"负面词 → {r2['change']}"); p += 1
        else: F(f"change={r2['change']}"); f += 1

        r3 = ie.evaluate("今天天气怎么样？", 50)
        if r3["change"] == 0: P("中性 → 0"); p += 1
        else: F(f"change={r3['change']}"); f += 1

        # ===== 3. /api/chat 返回 intimacy 字段 =====
        print("\n── /api/chat intimacy 字段 ──")
        r = client.post("/api/chat", json={
            "session_id": "s1", "message": "你好呀",
            "profile": {"intimacy": 50},
        })
        data = r.json()
        for key in ["intimacy_change", "intimacy", "intimacy_reason"]:
            if key in data: P(f"/api/chat 含 {key}"); p += 1
            else: F(f"缺 {key}"); f += 1
        if "_diag" not in data: P("安全审计S03: _diag 已移除"); p += 1
        else: F("_diag 字段仍存在，违反S03"); f += 1

        # ===== 4. KnowledgeFilter 三级过滤 =====
        print("\n── KnowledgeFilter 三级过滤 ──")
        from services.attribute_engine import KnowledgeFilter
        kf = KnowledgeFilter()
        # cirno filter (edu=-100)
        r = kf.filter("量子力学的薛定谔方程很难", -100)
        if "完全听不懂" in r: P("edu=-100 → cirno过滤"); p += 1
        else: F(f"返回={r[:40]}"); f += 1
        if "BAKA" in r: P("含 BAKA~"); p += 1
        else: F("缺 BAKA"); f += 1

        # low edu (edu≤-70)
        r2 = kf.filter("微积分和梯度下降", -80)
        if "不太懂" in r2: P("edu=-80 → 低文化过滤"); p += 1
        else: F(f"返回={r2[:40]}"); f += 1

        # domain restrict
        r3 = kf.filter("我今天学了微积分和神经网络", 0, ["艺术"])
        if "不太擅长" in r3: P("allowed_domains=['艺术'] → 非域词汇拦截"); p += 1
        else: F(f"返回={r3[:50]}"); f += 1

        # 正常通过
        r4 = kf.filter("今天天气真好", 50)
        if r4 == "今天天气真好": P("正常→原样通过"); p += 1
        else: F(f"返回={r4}"); f += 1

        # ===== 5. filter_response 修改 inner_thought =====
        print("\n── filter_response 修改 inner_thought ──")
        result = {"inner_thought": "原内心独白", "spoken": "量子力学好难理解"}
        out = kf.filter_response(result, -100)
        if "知识天花板" in out["inner_thought"]: P("过滤后inner_thought追加提示"); p += 1
        else: F(f"inner_thought={out['inner_thought']}"); f += 1

        # ===== 6. 10 组交叉效果 =====
        print("\n── 10 组交叉效果 ──")
        from services.attribute_engine import CrossEffectCalculator, MISSProfile
        calc = CrossEffectCalculator()
        for combo in CROSS:
            prof = MISSProfile(**combo["profile"])
            effects = calc.calculate(prof)
            ids = [e["id"] for e in effects]
            if combo["expected_id"] in ids:
                P(f"{combo['name']} → {combo['expected_id']}"); p += 1
            else: F(f"{combo['name']} 期望{combo['expected_id']} 实际{ids}"); f += 1

        # ===== 7. 模块导出完整性 =====
        print("\n── 模块导出 ──")
        from services import __all__ as ex
        expected_new = {"KnowledgeFilter", "IntimacyEngine"}
        if expected_new.issubset(set(ex)): P("KnowledgeFilter+IntimacyEngine 已导出"); p += 1
        else: F(f"缺: {expected_new - set(ex)}"); f += 1
        if len(ex) >= 13: P(f"services/__init__.py 含 {len(ex)} 个类"); p += 1
        else: F(f"仅{len(ex)}个"); f += 1

        # ===== 8. LLMCaller.flush_client() =====
        print("\n── LLMCaller.flush_client() ──")
        from services.llm_caller import LLMCaller
        lc = LLMCaller()
        lc._ensure_client()
        assert lc._client is not None, "客户端应该已创建"
        lc.flush_client()
        if lc._client is None: P("flush_client后_client=None"); p += 1
        else: F("_client未清空"); f += 1

        # ===== 9. StaticFiles 挂载 =====
        print("\n── StaticFiles 挂载 ──")
        r = client.get("/")
        if r.status_code == 200: P("GET / → 200 (StaticFiles)"); p += 1
        else: F(f"状态码={r.status_code}"); f += 1
        if "MISS" in r.text or "miss" in r.text.lower(): P("返回含 MISS 字样"); p += 1
        else: F("未找到MISS字样"); f += 1

        # ===== 10. /api/info 端点 =====
        print("\n── /api/info 端点 ──")
        r = client.get("/api/info")
        if r.status_code == 200: P("/api/info → 200"); p += 1
        else: F(f"状态码={r.status_code}"); f += 1
        info = r.json()
        if "endpoints" in info: P("含 endpoints 字段"); p += 1
        else: F("缺 endpoints"); f += 1
        if "chat_request_schema" in info: P("含 chat_request_schema"); p += 1
        else: F("缺 chat_request_schema"); f += 1


        # ===== 12. LLMCaller 懒加载 + base_url =====
        print("\n── LLMCaller 懒加载 + 自定义base_url ──")
        import inspect
        source = inspect.getsource(LLMCaller._ensure_client)
        if "get_api_key()" in source: P("_ensure_client 使用 get_api_key()"); p += 1
        else: F("未使用get_api_key()"); f += 1
        if "get_base_url()" in source: P("_ensure_client 使用 get_base_url()"); p += 1
        else: F("未使用get_base_url()"); f += 1
        if "get_model()" in source: P("call() 使用 get_model()"); p += 1
        else:
            source2 = inspect.getsource(LLMCaller.call)
            if "get_model()" in source2: P("call() 使用 get_model()"); p += 1
            else: F("未使用get_model()"); f += 1

        print("\n" + "=" * 65)
        t = p + f
        print(f"测试总数: {t}  通过: {p}  失败: {f}  通过率: {p/t*100:.1f}%")
        print("=" * 65)

    finally:
        Base.metadata.drop_all(bind=engine)
        try: os.remove("tests/data/test_new_features.db")
        except OSError: pass

    if f == 0: print("\n🎉 新功能验收通过！")
    else: print("\n❌ 新功能验收未通过！")
    return 0 if f == 0 else 1


# 10 组交叉效果 (已从5组扩展到10组)
CROSS = [
    {"name":"好奇笨蛋",  "profile":{"education_level":-100,"curiosity":100},                  "expected_id":"curious_baka"},
    {"name":"傲娇恋人",  "profile":{"independent_submissive":-100,"intimacy":100},              "expected_id":"tsundere_lover"},
    {"name":"感性喜剧人","profile":{"rational_emotional":100,"humor":100},                      "expected_id":"dramatic_comedian"},
    {"name":"暴走千金",  "profile":{"aggression":100,"willpower":-100},                         "expected_id":"volatile_heiress"},
    {"name":"孤胆冒险家","profile":{"social_energy":-100,"adventurousness":100},                "expected_id":"lone_adventurer"},
    {"name":"书呆子",    "profile":{"education_level":100,"curiosity":-100},                    "expected_id":"scholarly_bore"},
    {"name":"黏人精",    "profile":{"intimacy":100,"independent_submissive":100},                "expected_id":"clingy_koala"},
    {"name":"冰山美人",  "profile":{"rational_emotional":-100,"aggression":-100},               "expected_id":"ice_queen"},
    {"name":"派对狂人",  "profile":{"social_energy":100,"adventurousness":100},                 "expected_id":"party_animal"},
    {"name":"钢铁战士",  "profile":{"willpower":100,"aggression":100},                          "expected_id":"relentless_warrior"},
]


if __name__ == "__main__":
    sys.exit(run())
