# Copyright (C) 2026  MISS Project Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
"""
Phase 7 验收测试 - Task 7.1 (单元测试) + Task 7.2 (集成测试)
验收标准:
  7.1: pytest 全绿
  7.2: 3条端到端链路 - 对话/彩蛋/预设
"""
import json, os, sys, subprocess, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["DB_URL"] = "sqlite:///./tests/data/test_phase7.db"
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
        print("Phase 7 验收测试 - 测试与集成")
        print("=" * 65)

        # ================================================================
        # Task 7.1 单元测试
        # ================================================================
        print("\n" + "─" * 40 + " Task 7.1: 单元测试 " + "─" * 40)

        print("\n【7.1-1】pytest 全量执行")
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "-q", "--tb=line"],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            capture_output=True, text=True, timeout=300,
            env={**os.environ, "DB_URL": "sqlite:///./_phase7_test.db", "OPENAI_API_KEY": ""}
        )
        if result.returncode == 0:
            # extract passed count
            for line in result.stdout.strip().split("\n"):
                if "passed" in line.lower():
                    __ = line.strip()
            P("pytest 全量: 退出码=0 ✅"); p += 1
        else:
            F(f"pytest 退出码={result.returncode}"); f += 1
        print(f"    stdout: {result.stdout.strip()[-200:]}")

        # ================================================================
        # 7.1 子项验证: Pydantic边界 / 彩蛋触发 / 交叉影响 / JSON解析容错
        # ================================================================
        print("\n【7.1-2】Task 1.1: Pydantic 边界验证 (test_profile.py)")
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/test_profile.py", "-q"],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            capture_output=True, text=True, timeout=60,
            env={**os.environ, "DB_URL": "sqlite:///./_p7_test.db", "OPENAI_API_KEY": ""}
        )
        if result.returncode == 0: P("test_profile.py → 全部通过"); p += 1
        else: F(f"退出码={result.returncode}"); f += 1

        print("\n【7.1-3】Task 1.2: 彩蛋触发/解除 (test_easter_egg.py)")
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/test_easter_egg.py", "-q"],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            capture_output=True, text=True, timeout=60,
            env={**os.environ, "DB_URL": "sqlite:///./_p7_test.db", "OPENAI_API_KEY": ""}
        )
        if result.returncode == 0: P("test_easter_egg.py → 全部通过"); p += 1
        else: F(f"退出码={result.returncode}"); f += 1

        print("\n【7.1-4】Task 1.3: 交叉影响正确匹配 (test_cross_effects.py)")
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/test_cross_effects.py", "-q"],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            capture_output=True, text=True, timeout=60,
            env={**os.environ, "DB_URL": "sqlite:///./_p7_test.db", "OPENAI_API_KEY": ""}
        )
        if result.returncode == 0: P("test_cross_effects.py → 全部通过"); p += 1
        else: F(f"退出码={result.returncode}"); f += 1

        print("\n【7.1-5】Task 2.3: JSON 解析容错 (test_llm_json_parse.py)")
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/test_llm_json_parse.py", "-q"],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            capture_output=True, text=True, timeout=60,
            env={**os.environ, "DB_URL": "sqlite:///./_p7_test.db", "OPENAI_API_KEY": ""}
        )
        if result.returncode == 0: P("test_llm_json_parse.py → 全部通过"); p += 1
        else: F(f"退出码={result.returncode}"); f += 1

        # ================================================================
        # Task 7.2 集成测试 - 链路1: 对话端到端
        # ================================================================
        print("\n" + "─" * 40 + " Task 7.2: 集成测试 " + "─" * 40)
        print("\n【7.2-1】链路1: POST /api/chat → PromptBuilder → LLMCaller → 降级返回")

        r = client.post("/api/chat", json={
            "session_id": "e2e_chat", "message": "今天心情怎么样？",
            "profile": {"rational_emotional": 30, "intimacy": 60},
        })
        if r.status_code == 200: P("POST /api/chat → 200"); p += 1
        else: F(f"状态码={r.status_code}"); f += 1

        data = r.json()
        for field in ["inner_thought", "spoken", "active_easter_eggs", "active_cross_effects"]:
            if field in data: P(f"含字段: {field}"); p += 1
            else: F(f"缺字段: {field}"); f += 1

        if isinstance(data["spoken"], str) and len(data["spoken"]) > 0:
            P("spoken 非空字符串 → 降级回应成功"); p += 1
        else: F("spoken 为空"); f += 1

        if isinstance(data["active_easter_eggs"], list): P("easter_eggs 为 list"); p += 1
        else: F("easter_eggs 类型错误"); f += 1
        if isinstance(data["active_cross_effects"], list): P("cross_effects 为 list"); p += 1
        else: F("cross_effects 类型错误"); f += 1

        # ================================================================
        # 链路2: 彩蛋端到端
        # ================================================================
        print("\n【7.2-2】链路2: education_level=-100 → ⑨模式 → 响应含cirno_mode")

        r = client.post("/api/chat", json={
            "session_id": "e2e_cirno", "message": "什么是量子物理？",
            "profile": {"education_level": -100},
        })
        if r.status_code == 200: P("⑨模式 POST → 200"); p += 1
        else: F(f"状态码={r.status_code}"); f += 1

        data = r.json()
        if "cirno_mode" in data["active_easter_eggs"]:
            P("active_easter_eggs 含 cirno_mode (⑨触发)"); p += 1
        else: F(f"eggs={data['active_easter_eggs']}"); f += 1

        # 未设置⑨ → 无彩蛋
        r2 = client.post("/api/chat", json={
            "session_id": "e2e_no", "message": "你好",
            "profile": {},
        })
        if "cirno_mode" not in r2.json()["active_easter_eggs"]:
            P("默认profile → 无cirno_mode (⑨未误触发)"); p += 1
        else: F("默认profile误触发cirno_mode"); f += 1

        # ================================================================
        # 链路3: 预设端到端
        # ================================================================
        print("\n【7.2-3】链路3: 预设保存 → 加载 → 确认属性一致")

        # Step1: 保存预设
        original = {
            "rational_emotional": 50, "willpower": 30,
            "education_level": -100, "intimacy": 80,
            "curiosity": 100, "humor": 90,
            "aggression": -50, "allowed_domains": ["科学", "艺术"],
        }
        r = client.post("/api/preset/save", json={"name": "⑨好奇亲密预设", "profile": original})
        preset_id = r.json()["id"]
        P(f"保存预设 id={preset_id}"); p += 1

        # Step2: 列表验证存在
        r = client.get("/api/preset/list")
        preset_ids = [p["id"] for p in r.json()["presets"]]
        if preset_id in preset_ids: P("预设存在于列表中"); p += 1
        else: F("预设不在列表"); f += 1

        # Step3: 读取预设
        r = client.get(f"/api/preset/{preset_id}")
        loaded = r.json()["profile"]
        if loaded.get("education_level") == -100: P("加载后 edu=-100"); p += 1
        else: F(f"edu={loaded.get('education_level')}"); f += 1
        if loaded.get("curiosity") == 100: P("加载后 curiosity=100"); p += 1
        else: F(f"cur={loaded.get('curiosity')}"); f += 1
        if loaded.get("allowed_domains") == ["科学", "艺术"]:
            P("加载后 allowed_domains=['科学','艺术']"); p += 1
        else: F(f"domains={loaded.get('allowed_domains')}"); f += 1

        # Step4: 应用预设到对话
        r = client.post("/api/preset/apply", json={"preset_id": preset_id})
        apply_result = r.json()
        if r.status_code == 200: P("apply预设 → 200"); p += 1
        else: F(f"状态码={r.status_code}"); f += 1
        if apply_result["profile"]["education_level"] == -100: P("apply后 profile 属性一致"); p += 1
        else: F("apply后属性不一致"); f += 1

        # Step5: 预设导入导出往返
        print("\n【7.2-4】附加: 预设导入导出往返验证")
        r = client.get(f"/api/preset/{preset_id}/export")
        exported = r.json()
        if "version" in exported and exported["version"] == "1.0":
            P("导出格式正确 (version=1.0)"); p += 1
        else: F(f"导出格式错误"); f += 1

        # 导入
        import json, io
        files = {"file": ("test.json", io.BytesIO(json.dumps(exported, ensure_ascii=False).encode("utf-8")), "application/json")}
        r = client.post("/api/preset/import", files=files)
        if r.status_code == 200: P("导入导出预设 → 200"); p += 1
        else: F(f"状态码={r.status_code}"); f += 1
        imported = r.json()["profile"]
        if imported.get("education_level") == -100: P("导入后 edu=-100 保留"); p += 1
        else: F(f"edu={imported.get('education_level')}"); f += 1

        # ================================================================
        # 汇总
        # ================================================================
        print("\n" + "=" * 65)
        t = p + f
        print(f"测试总数: {t}  通过: {p}  失败: {f}  通过率: {p/t*100:.1f}%")
        print("=" * 65)

    finally:
        Base.metadata.drop_all(bind=engine)
        try:
            os.remove("tests/data/test_phase7.db")
            os.remove("_phase7_test.db")
        except OSError:
            pass

    if f == 0: print("\n🎉 Phase 7 验收通过！")
    else: print("\n❌ Phase 7 验收未通过！")
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(run())
