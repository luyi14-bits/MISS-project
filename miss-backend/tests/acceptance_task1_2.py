# Copyright (C) 2026  MISS Project Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
"""
Task 1.2 严格验收测试 - 彩蛋系统：⑨模式触发器
验收标准：education_level=-100 返回 cirno_mode，调至 -99 后返回空 dict
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.attribute_engine import MISSProfile, EasterEggEngine


def print_pass(test_name):
    print(f"  ✅ PASS: {test_name}")


def print_fail(test_name, detail=""):
    print(f"  ❌ FAIL: {test_name}")
    if detail:
        print(f"     {detail}")


CIRNO_CONFIG = {
    "name_suffix": "⑨",
    "catchphrase": "BAKA~",
    "catchphrase_frequency": 0.25,
    "name_color": "#00BFFF",
    "avatar_decor": "ice_crystal_wings",
    "knowledge_fallback": "simple_confusion",
    "wrong_answer_probability": 0.30,
}


def run_acceptance_tests():
    passed = 0
    failed = 0
    engine = EasterEggEngine()

    print("=" * 60)
    print("Task 1.2 验收测试 - 彩蛋系统：⑨模式触发器")
    print("=" * 60)

    # ========== 测试1：类结构与签名 ==========
    print("\n【测试1】类结构与方法签名")
    try:
        assert hasattr(EasterEggEngine, "evaluate"), "缺少 evaluate 方法"
        print_pass("EasterEggEngine 类存在且有 evaluate 方法")
        passed += 1
    except AssertionError as e:
        print_fail(str(e))
        failed += 1

    try:
        import inspect
        sig = inspect.signature(engine.evaluate)
        params = list(sig.parameters.keys())
        assert "profile" in params, "方法缺少 profile 参数"
        assert sig.return_annotation == dict, f"返回类型应为 dict，实际为 {sig.return_annotation}"
        print_pass("evaluate(profile: MISSProfile) -> dict 签名正确")
        passed += 1
    except Exception as e:
        print_fail("方法签名检查失败", str(e))
        failed += 1

    try:
        engine_instance = EasterEggEngine()
        print_pass("EasterEggEngine 可正常实例化")
        passed += 1
    except Exception as e:
        print_fail("实例化失败", str(e))
        failed += 1

    # ========== 测试2：核心触发条件（education_level == -100）==========
    print("\n【测试2】核心触发：education_level=-100")
    try:
        profile = MISSProfile(education_level=-100)
        eggs = engine.evaluate(profile)
        assert isinstance(eggs, dict), f"返回类型应为 dict，实际为 {type(eggs).__name__}"
        assert "cirno_mode" in eggs, "未找到 cirno_mode 彩蛋"
        print_pass("education_level=-100 触发 cirno_mode 彩蛋")
        passed += 1
    except AssertionError as e:
        print_fail(str(e))
        failed += 1
    except Exception as e:
        print_fail("触发测试异常", str(e))
        failed += 1

    # ========== 测试3：cirno_mode 子字段完整性 ==========
    print("\n【测试3】cirno_mode 子字段完整性")
    profile = MISSProfile(education_level=-100)
    eggs = engine.evaluate(profile)
    cm = eggs.get("cirno_mode", {})

    for field, expected_value in CIRNO_CONFIG.items():
        try:
            assert field in cm, f"缺少字段 {field}"
            actual = cm[field]
            assert actual == expected_value, f"{field} 期望 {expected_value!r}，实际 {actual!r}"
            print_pass(f"cirno_mode.{field} = {expected_value!r}")
            passed += 1
        except AssertionError as e:
            print_fail(str(e))
            failed += 1

    # 额外检查：不允许有多余字段
    extra_fields = set(cm.keys()) - set(CIRNO_CONFIG.keys())
    if extra_fields:
        print_fail(f"cirno_mode 包含未定义字段: {extra_fields}")
        failed += 1
    else:
        print_pass("cirno_mode 无多余字段，字段数=7")
        passed += 1

    # ========== 测试4：非触发值返回空 ==========
    print("\n【测试4】非触发值返回空 dict")
    non_trigger_values = [-101, -100, -99, -50, -1, 0, 1, 50, 99, 100, 101]

    for val in non_trigger_values:
        try:
            profile = MISSProfile(education_level=val)
        except Exception:
            # -101 和 101 应该在创建 MISSProfile 时就抛异常
            continue

        eggs = engine.evaluate(profile)
        if val == -100:
            # -100 应该触发
            try:
                assert "cirno_mode" in eggs, f"education_level={val} 应触发"
                print_pass(f"education_level={val} → cirno_mode 触发（预期行为）")
                passed += 1
            except AssertionError as e:
                print_fail(str(e))
                failed += 1
        else:
            # 其他值不应触发
            try:
                assert eggs == {}, f"education_level={val} 不应触发，但返回了 {eggs}"
                print_pass(f"education_level={val} → 空 dict（预期行为）")
                passed += 1
            except AssertionError as e:
                print_fail(str(e))
                failed += 1

    # ========== 测试5：其他属性不影响触发 ==========
    print("\n【测试5】其他属性不影响 cirno 触发")
    test_profiles = [
        # (描述, profile_kwargs)
        ("仅 education_level=-100", {"education_level": -100}),
        ("全部属性极端值 + edu=-100", {
            "education_level": -100, "rational_emotional": 100,
            "willpower": 100, "independent_submissive": -100,
            "curiosity": 100, "humor": -100, "aggression": 100,
            "social_energy": 100, "adventurousness": -100,
            "intimacy": 100,
        }),
        ("全部属性极端值 + edu=0", {
            "education_level": 0, "rational_emotional": 100,
            "willpower": 100, "independent_submissive": -100,
            "curiosity": 100, "humor": -100, "aggression": 100,
            "social_energy": 100, "adventurousness": -100,
            "intimacy": 100,
        }),
    ]

    for desc, kwargs in test_profiles:
        try:
            profile = MISSProfile(**kwargs)
            eggs = engine.evaluate(profile)
            if profile.education_level == -100:
                assert "cirno_mode" in eggs, f"{desc}: 应触发"
                print_pass(f"{desc} → 正确触发")
            else:
                assert eggs == {}, f"{desc}: 不应触发，实际 {eggs}"
                print_pass(f"{desc} → 正确不触发")
            passed += 1
        except AssertionError as e:
            print_fail(str(e))
            failed += 1

    # ========== 测试6：返回类型始终为 dict ==========
    print("\n【测试6】返回类型始终为 dict")
    for val in [-100, -99, 0, 50, 100]:
        try:
            profile = MISSProfile(education_level=val)
        except Exception:
            continue
        eggs = engine.evaluate(profile)
        try:
            assert isinstance(eggs, dict), f"education_level={val} 返回 {type(eggs).__name__}"
            print_pass(f"education_level={val} 返回 dict 类型")
            passed += 1
        except AssertionError as e:
            print_fail(str(e))
            failed += 1

    # ========== 测试7：无状态/幂等性 ==========
    print("\n【测试7】无状态与幂等性")
    try:
        profile = MISSProfile(education_level=-100)
        result1 = engine.evaluate(profile)
        result2 = engine.evaluate(profile)
        result3 = engine.evaluate(profile)
        assert result1 == result2 == result3, "多次调用结果不一致"
        print_pass("多次调用结果一致（幂等性通过）")
        passed += 1
    except AssertionError as e:
        print_fail(str(e))
        failed += 1

    # ========== 测试8：import 可用性 ==========
    print("\n【测试8】模块导入可用性")
    try:
        from services.attribute_engine import EasterEggEngine as E2
        e2 = E2()
        result = e2.evaluate(MISSProfile(education_level=-100))
        assert "cirno_mode" in result
        print_pass("EasterEggEngine 从 attribute_engine 正常导入并使用")
        passed += 1
    except Exception as e:
        print_fail("从 attribute_engine 导入失败", str(e))
        failed += 1

    # 检查 services/__init__.py 是否导出
    try:
        from services import EasterEggEngine as E3
        print_pass("EasterEggEngine 已从 services/__init__.py 导出")
        passed += 1
    except ImportError:
        print_fail(
            "EasterEggEngine 未在 services/__init__.py 导出",
            "应添加: from .attribute_engine import EasterEggEngine"
        )
        failed += 1

    # ========== 汇总 ==========
    print("\n" + "=" * 60)
    total = passed + failed
    print(f"测试总数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"通过率: {passed/total*100:.1f}%")
    print("=" * 60)

    if failed == 0:
        print("\n🎉 Task 1.2 验收通过！")
        return 0
    else:
        print("\n❌ Task 1.2 验收未通过！")
        return 1


if __name__ == "__main__":
    sys.exit(run_acceptance_tests())
