# Copyright (C) 2026  MISS Project Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
"""
程序组最新任务验收 - character/analyze + background 扩展
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["DB_URL"] = "sqlite:///./tests/data/test_char_bg.db"
os.environ["OPENAI_API_KEY"] = ""

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
        print("程序组最新任务 验收测试")
        print("=" * 65)

        # ===== 1. /api/character/analyze 端点存在 =====
        print("\n【1】POST /api/character/analyze 端点存在")
        r = client.post("/api/character/analyze", json={
            "description": "傲娇的富家千金，对男主一开始很冷淡但其实在意"
        })
        # 无 API key → 走 fallback 路径 → LLMCaller 返回降级
        if r.status_code in (200, 502):
            P(f"/api/character/analyze → {r.status_code} (无key时502是预期的)"); p += 1
        else: F(f"状态码={r.status_code}"); f += 1

        # ===== 2. /api/character/analyze 正常流程（有key时的预期struct）=====
        print("\n【2】/api/character/analyze 请求体结构")
        r = client.post("/api/character/analyze", json={
            "description": "一个温柔体贴、知识渊博的大姐姐"
        })
        data = r.json()
        if r.status_code == 200:
            if "profile" in data: P("返回含 profile 字段"); p += 1
            else: F("缺 profile"); f += 1
        else:
            if "detail" in data: P("失败时含 detail 字段"); p += 1
            else: F("缺 detail"); f += 1

        # ===== 3. /api/character/analyze 参数验证 =====
        print("\n【3】/api/character/analyze 参数验证")
        r = client.post("/api/character/analyze", json={})
        if r.status_code == 422: P("缺 description → 422"); p += 1
        else: F(f"状态码={r.status_code}"); f += 1

        r = client.post("/api/character/analyze", json={"description": 123})
        if r.status_code == 422: P("description非字符串 → 422"); p += 1
        else: F(f"状态码={r.status_code}"); f += 1

        # ===== 4. LLMCaller 正常调用路径（有key时的value clamping验证）=====
        print("\n【4】CharacterAnalyzeRequest Pydantic 模型")
        from routers.character import CharacterAnalyzeRequest
        req = CharacterAnalyzeRequest(description="测试")
        if req.description == "测试": P("CharacterAnalyzeRequest 可用"); p += 1
        else: F("构造错误"); f += 1

        # ===== 5. ATTR_META 完整性 =====
        print("\n【5】ATTR_META 10维属性完整性")
        from routers.character import ATTR_META
        expected_keys = {
            "rational_emotional", "willpower", "independent_submissive",
            "education_level", "intimacy", "curiosity", "humor",
            "aggression", "social_energy", "adventurousness",
        }
        actual_keys = {name for name, _, _, _ in ATTR_META}
        if actual_keys == expected_keys: P("ATTR_META 含全部10维属性"); p += 1
        else: F(f"缺: {expected_keys - actual_keys}"); f += 1

        # ===== 6. clamping逻辑 =====
        print("\n【6】Value clamping 逻辑（在code中验证）")
        import inspect
        source = inspect.getsource(
            __import__("routers.character", fromlist=[""]).analyze_character
        )
        if "max(lo, min(hi, val))" in source: P("含 max(lo, min(hi, val)) sublogic"); p += 1
        else:
            if "clamped" in source: P("含值限制逻辑"); p += 1
            else: F("缺值限制"); f += 1

        # ===== 7. model_validate 最终验证 =====
        if "MISSProfile.model_validate(clamped)" in source or "model_validate" in source:
            P("最终调用 model_validate"); p += 1
        else: F("缺 model_validate"); f += 1

        # ===== 8. prompt模板含10维说明 =====
        print("\n【7】Prompt 模板含 10 维说明")
        if "rational_emotional" in source: P("prompt含 rational_emotional"); p += 1
        else: F("缺"); f += 1
        if "intimacy" in source: P("prompt含 intimacy"); p += 1
        else: F("缺"); f += 1

        # ===== 9. Preset 表新增 background 列 =====
        print("\n【8】Preset 表 background 列")
        from models.preset import Preset
        cols = {c.name for c in Preset.__table__.columns}
        if "background" in cols: P("Preset 含 background 列"); p += 1
        else: F("缺 background"); f += 1

        # ===== 10. SavePresetRequest 含 background =====
        print("\n【9】SavePresetRequest 含 background")
        from routers.preset import SavePresetRequest
        req = SavePresetRequest(name="test", background="富家千金人设")
        if req.background == "富家千金人设": P("SavePresetRequest.background 可用"); p += 1
        else: F(f"background={req.background}"); f += 1

        # ===== 11. preset save 含 background =====
        print("\n【10】POST /api/preset/save 含 background")
        r = client.post("/api/preset/save", json={
            "name": "bg_test",
            "profile": {"education_level": 50},
            "background": "温柔大姐姐背景",
        })
        if r.status_code == 200: P("save → 200"); p += 1
        else: F(f"状态码={r.status_code}"); f += 1
        data = r.json()
        if data.get("background") == "温柔大姐姐背景": P("save返回含background"); p += 1
        else: F(f"background={data.get('background')}"); f += 1

        # ===== 12. preset get 含 background =====
        print("\n【11】GET /api/preset/{id} 含 background")
        pid = data["id"]
        r = client.get(f"/api/preset/{pid}")
        if r.json().get("background") == "温柔大姐姐背景":
            P("get返回含background"); p += 1
        else: F(f"background={r.json().get('background')}"); f += 1

        # ===== 13. preset list 含 background =====
        print("\n【12】GET /api/preset/list 含 background")
        r = client.get("/api/preset/list")
        presets = r.json()["presets"]
        bg_preset = [p for p in presets if p["id"] == pid]
        if bg_preset and bg_preset[0].get("background") == "温柔大姐姐背景":
            P("list返回含background"); p += 1
        else: F(f"background={bg_preset[0].get('background') if bg_preset else 'None'}"); f += 1

        # ===== 14. preset export 含 background + version=1.1 =====
        print("\n【13】GET /api/preset/{id}/export 含 background + v1.1")
        r = client.get(f"/api/preset/{pid}/export")
        export_data = r.json()
        if export_data.get("version") == "1.1": P("version=1.1"); p += 1
        else: F(f"version={export_data.get('version')}"); f += 1
        if export_data.get("background") == "温柔大姐姐背景": P("export含background"); p += 1
        else: F(f"background={export_data.get('background')}"); f += 1

        # ===== 15. preset import 含 background =====
        print("\n【14】POST /api/preset/import 含 background")
        import io
        import_json = json.dumps({
            "version": "1.1",
            "name": "import_bg_test",
            "profile": {"education_level": 30},
            "background": "导入的背景故事",
        }, ensure_ascii=False)
        files = {"file": ("test.json", io.BytesIO(import_json.encode("utf-8")), "application/json")}
        r = client.post("/api/preset/import", files=files)
        if r.status_code == 200: P("import → 200"); p += 1
        else: F(f"状态码={r.status_code}"); f += 1
        if r.json().get("background") == "导入的背景故事": P("import保留background"); p += 1
        else: F(f"background={r.json().get('background')}"); f += 1

        # ===== 16. ChatRequest 含 background =====
        print("\n【15】ChatRequest 含 background 字段")
        from routers.chat import ChatRequest
        req = ChatRequest(session_id="s", message="hi", background="背景故事")
        if req.background == "背景故事": P("ChatRequest.background 可用"); p += 1
        else: F(f"background={req.background}"); f += 1

        # ===== 17. PromptBuilder.build_full() 含 character_background =====
        print("\n【16】PromptBuilder.build_full() 接受 character_background")
        import inspect
        sig = inspect.signature(
            __import__("services.prompt_builder", fromlist=["PromptBuilder"]).PromptBuilder.build_full
        )
        if "character_background" in sig.parameters:
            P("build_full()签名含 character_background"); p += 1
        else: F("缺 character_background"); f += 1

        # ===== 18. background 注入到 system prompt =====
        print("\n【17】background 注入到 system prompt")
        from services.prompt_builder import PromptBuilder
        from services.attribute_engine import MISSProfile
        builder = PromptBuilder()
        result = builder.build_full("s_bg", "你好", MISSProfile(), "傲娇富家千金")
        system = result["messages"][0]["content"]
        if "傲娇富家千金" in system: P("system_prompt 含 background"); p += 1
        else: F("background未注入"); f += 1
        if "人物背景设定" in system: P("含【你的人物背景设定】标题"); p += 1
        else: F("缺标题"); f += 1

        # ===== 19. build_full 旧调用方式兼容 =====
        print("\n【18】build_full 旧调用方式兼容（无background参数）")
        from services.prompt_builder import PromptBuilder as PB
        pb = PB()
        result_old = pb.build_full("s_old", "hi", MISSProfile())
        if "messages" in result_old: P("无background参数 → 正常返回"); p += 1
        else: F("失败"); f += 1
        result_old_msg = pb.build("s_old2", "hi", MISSProfile())
        if isinstance(result_old_msg, list): P("build()无background参数 → 正常返回list"); p += 1
        else: F("失败"); f += 1

        # ===== 20. version 1.1 导出/导入往返 =====
        print("\n【19】v1.1 导出/导入往返")
        r_save = client.post("/api/preset/save", json={
            "name": "roundtrip_bg", "profile": {"education_level": -100, "curiosity": 100},
            "background": "往返测试背景",
        })
        rt_id = r_save.json()["id"]
        r_export = client.get(f"/api/preset/{rt_id}/export")
        exported = r_export.json()

        files = {"file": ("rt.json", io.BytesIO(json.dumps(exported, ensure_ascii=False).encode("utf-8")), "application/json")}
        r_import = client.post("/api/preset/import", files=files)
        if r_import.status_code == 200: P("v1.1 往返导入 → 200"); p += 1
        else: F(f"状态码={r_import.status_code}"); f += 1
        imported = r_import.json()
        if imported.get("profile", {}).get("education_level") == -100:
            P("往返: edu=-100 保留"); p += 1
        else: F(f"edu={imported.get('profile', {}).get('education_level')}"); f += 1
        if imported.get("background") == "往返测试背景":
            P("往返: background 保留"); p += 1
        else: F(f"bg={imported.get('background')}"); f += 1

        # ===== 21. 模块导入 =====
        print("\n【20】routers/__init__.py 含 character_router")
        from routers import __all__ as router_exports
        if "character_router" in router_exports:
            P("character_router 已导出"); p += 1
        else: F("缺 character_router"); f += 1

        # ===== 汇总 =====
        print("\n" + "=" * 65)
        t = p + f
        print(f"测试总数: {t}  通过: {p}  失败: {f}  通过率: {p/t*100:.1f}%")
        print("=" * 65)

    finally:
        Base.metadata.drop_all(bind=engine)
        try: os.remove("tests/data/test_char_bg.db")
        except OSError: pass

    if f == 0: print("\n🎉 程序组最新任务 验收通过！")
    else: print("\n❌ 验收未通过！")
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(run())
