"""
Task 1.1 严格验收测试 - MISS属性数据模型
验收标准：正负边界值能通过验证，超界抛 ValidationError
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import BaseModel, Field, ValidationError
from services.attribute_engine import MISSProfile


def print_pass(test_name):
    print(f"  ✅ PASS: {test_name}")


def print_fail(test_name, detail=""):
    print(f"  ❌ FAIL: {test_name}")
    if detail:
        print(f"     {detail}")


def run_acceptance_tests():
    passed = 0
    failed = 0

    print("=" * 60)
    print("Task 1.1 验收测试 - MISS属性数据模型")
    print("=" * 60)

    # ==================== 测试1：10维字段完整性 ====================
    print("\n【测试1】10维属性字段完整性检查")
    expected_fields = [
        "rational_emotional",
        "willpower",
        "independent_submissive",
        "education_level",
        "intimacy",
        "curiosity",
        "humor",
        "aggression",
        "social_energy",
        "adventurousness",
    ]
    actual_fields = list(MISSProfile.model_fields.keys())

    all_fields_ok = True
    for field in expected_fields:
        if field in actual_fields:
            print_pass(f"字段 {field} 存在")
            passed += 1
        else:
            print_fail(f"字段 {field} 缺失")
            failed += 1
            all_fields_ok = False

    if "allowed_domains" in actual_fields:
        print_pass("字段 allowed_domains 存在")
        passed += 1
    else:
        print_fail("字段 allowed_domains 缺失")
        failed += 1
        all_fields_ok = False

    # ==================== 测试2：默认值检查 ====================
    print("\n【测试2】默认值检查")
    try:
        profile = MISSProfile()
        for field in expected_fields:
            val = getattr(profile, field)
            if val == 0:
                print_pass(f"{field} 默认值为 0")
                passed += 1
            else:
                print_fail(f"{field} 默认值错误，期望0，实际{val}")
                failed += 1

        if profile.allowed_domains == []:
            print_pass("allowed_domains 默认值为空列表")
            passed += 1
        else:
            print_fail(f"allowed_domains 默认值错误，期望[]，实际{profile.allowed_domains}")
            failed += 1
    except Exception as e:
        print_fail("创建默认实例失败", str(e))
        failed += 11

    # ==================== 测试3：类型检查 ====================
    print("\n【测试3】字段类型检查")
    try:
        profile = MISSProfile()
        for field in expected_fields:
            val = getattr(profile, field)
            if isinstance(val, int):
                print_pass(f"{field} 类型为 int")
                passed += 1
            else:
                print_fail(f"{field} 类型错误，期望int，实际{type(val).__name__}")
                failed += 1

        if isinstance(profile.allowed_domains, list):
            print_pass("allowed_domains 类型为 list")
            passed += 1
        else:
            print_fail(f"allowed_domains 类型错误，期望list，实际{type(profile.allowed_domains).__name__}")
            failed += 1
    except Exception as e:
        print_fail("类型检查失败", str(e))
        failed += 1

    # ==================== 测试4：正向边界值 (+100) 验证 ====================
    print("\n【测试4】正向边界值 (+100) 验证")
    for field in expected_fields:
        try:
            kwargs = {field: 100}
            profile = MISSProfile(**kwargs)
            val = getattr(profile, field)
            if val == 100:
                print_pass(f"{field}=100 有效")
                passed += 1
            else:
                print_fail(f"{field}=100 验证错误，实际值{val}")
                failed += 1
        except ValidationError as e:
            print_fail(f"{field}=100 抛出ValidationError（不应抛出）", str(e)[:100])
            failed += 1
        except Exception as e:
            print_fail(f"{field}=100 未知错误", str(e))
            failed += 1

    # ==================== 测试5：负向边界值 (-100) 验证（亲密度除外） ====================
    print("\n【测试5】负向边界值 (-100) 验证（亲密度除外）")
    for field in expected_fields:
        if field == "intimacy":
            continue
        try:
            kwargs = {field: -100}
            profile = MISSProfile(**kwargs)
            val = getattr(profile, field)
            if val == -100:
                print_pass(f"{field}=-100 有效")
                passed += 1
            else:
                print_fail(f"{field}=-100 验证错误，实际值{val}")
                failed += 1
        except ValidationError as e:
            print_fail(f"{field}=-100 抛出ValidationError（不应抛出）", str(e)[:100])
            failed += 1
        except Exception as e:
            print_fail(f"{field}=-100 未知错误", str(e))
            failed += 1

    # ==================== 测试6：亲密度边界值验证（0 ~ 100，无负值） ====================
    print("\n【测试6】亲密度边界值验证（单向 0~100）")
    # 上边界
    try:
        profile = MISSProfile(intimacy=100)
        if profile.intimacy == 100:
            print_pass("intimacy=100 有效")
            passed += 1
        else:
            print_fail(f"intimacy=100 验证错误，实际值{profile.intimacy}")
            failed += 1
    except ValidationError:
        print_fail("intimacy=100 抛出ValidationError（不应抛出）")
        failed += 1

    # 下边界（0）
    try:
        profile = MISSProfile(intimacy=0)
        if profile.intimacy == 0:
            print_pass("intimacy=0 有效")
            passed += 1
        else:
            print_fail(f"intimacy=0 验证错误，实际值{profile.intimacy}")
            failed += 1
    except ValidationError:
        print_fail("intimacy=0 抛出ValidationError（不应抛出）")
        failed += 1

    # ==================== 测试7：正向超界 (+101) 应抛 ValidationError ====================
    print("\n【测试7】正向超界 (+101) 应抛 ValidationError")
    for field in expected_fields:
        try:
            kwargs = {field: 101}
            profile = MISSProfile(**kwargs)
            print_fail(f"{field}=101 未抛出ValidationError（应抛出）")
            failed += 1
        except ValidationError:
            print_pass(f"{field}=101 正确抛出ValidationError")
            passed += 1
        except Exception as e:
            print_fail(f"{field}=101 抛出未知错误而非ValidationError", str(e))
            failed += 1

    # ==================== 测试8：负向超界 (-101) 应抛 ValidationError（亲密度特殊处理） ====================
    print("\n【测试8】负向超界 (-101) 应抛 ValidationError")
    for field in expected_fields:
        if field == "intimacy":
            continue
        try:
            kwargs = {field: -101}
            profile = MISSProfile(**kwargs)
            print_fail(f"{field}=-101 未抛出ValidationError（应抛出）")
            failed += 1
        except ValidationError:
            print_pass(f"{field}=-101 正确抛出ValidationError")
            passed += 1
        except Exception as e:
            print_fail(f"{field}=-101 抛出未知错误而非ValidationError", str(e))
            failed += 1

    # 亲密度负向超界（-1）
    try:
        profile = MISSProfile(intimacy=-1)
        print_fail("intimacy=-1 未抛出ValidationError（应抛出）")
        failed += 1
    except ValidationError:
        print_pass("intimacy=-1 正确抛出ValidationError")
        passed += 1
    except Exception as e:
        print_fail("intimacy=-1 抛出未知错误而非ValidationError", str(e))
        failed += 1

    # ==================== 测试9：allowed_domains 功能验证 ====================
    print("\n【测试9】allowed_domains 功能验证")
    try:
        profile = MISSProfile(allowed_domains=["艺术", "人文", "科学"])
        if profile.allowed_domains == ["艺术", "人文", "科学"]:
            print_pass("allowed_domains 多值设置正常")
            passed += 1
        else:
            print_fail(f"allowed_domains 值错误，实际{profile.allowed_domains}")
            failed += 1
    except Exception as e:
        print_fail("allowed_domains 设置失败", str(e))
        failed += 1

    # 空列表
    try:
        profile = MISSProfile(allowed_domains=[])
        if profile.allowed_domains == []:
            print_pass("allowed_domains 空列表正常")
            passed += 1
        else:
            print_fail(f"allowed_domains 空列表错误，实际{profile.allowed_domains}")
            failed += 1
    except Exception as e:
        print_fail("allowed_domains 空列表失败", str(e))
        failed += 1

    # ==================== 测试10：模型序列化/反序列化 ====================
    print("\n【测试10】模型序列化/反序列化")
    try:
        profile = MISSProfile(
            rational_emotional=50,
            willpower=-30,
            education_level=-100,
            intimacy=80,
            allowed_domains=["艺术"],
        )
        json_str = profile.model_dump_json()
        profile2 = MISSProfile.model_validate_json(json_str)
        if profile2.rational_emotional == 50 and profile2.education_level == -100:
            print_pass("JSON序列化/反序列化正常")
            passed += 1
        else:
            print_fail("JSON序列化/反序列化结果不一致")
            failed += 1
    except Exception as e:
        print_fail("JSON序列化/反序列化失败", str(e))
        failed += 1

    # ==================== 汇总 ====================
    print("\n" + "=" * 60)
    total = passed + failed
    print(f"测试总数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"通过率: {passed/total*100:.1f}%")
    print("=" * 60)

    if failed == 0:
        print("\n🎉 Task 1.1 验收通过！")
        return 0
    else:
        print("\n❌ Task 1.1 验收未通过！")
        return 1


if __name__ == "__main__":
    sys.exit(run_acceptance_tests())
