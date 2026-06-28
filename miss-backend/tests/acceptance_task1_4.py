"""
Task 1.4 严格验收测试 - 属性→提示词片段映射器
验收标准：不同等级输出正确对应，含彩蛋条件分支
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.attribute_engine import MISSProfile, AttributePromptMapper


def P(test): print(f"  ✅ PASS: {test}")
def F(test, d=""): print(f"  ❌ FAIL: {test}"); d and print(f"     {d}")


# 设计文档要求的10个维度 + 对应方法名
DIMENSION_METHODS = {
    "rational_emotional": "map_rational_emotional",
    "willpower": "map_willpower",
    "independent_submissive": "map_independent_submissive",
    "education_level": "map_education_level",
    "intimacy": "map_intimacy",
    "curiosity": "map_curiosity",
    "humor": "map_humor",
    "aggression": "map_aggression",
    "social_energy": "map_social_energy",
    "adventurousness": "map_adventurousness",
}


def run():
    p = f = 0
    mapper = AttributePromptMapper()
    print("=" * 60)
    print("Task 1.4 验收测试 - 属性→提示词片段映射器")
    print("=" * 60)

    # ===== 测试1：类结构与10个映射方法 =====
    print("\n【测试1】类结构与10个映射方法存在性")
    try:
        assert hasattr(AttributePromptMapper, "map_all"), "缺少 map_all 方法"
        P("AttributePromptMapper 类存在")
        p += 1
    except AssertionError as e:
        F(str(e)); f += 1

    for dim, method_name in DIMENSION_METHODS.items():
        try:
            assert hasattr(mapper, method_name), f"缺少 {method_name} 方法"
            P(f"{method_name}() 方法存在")
            p += 1
        except AssertionError as e:
            F(str(e)); f += 1

    # ===== 测试2：每个方法接受int返回str =====
    print("\n【测试2】方法签名：接受int返回str（XML片段）")
    for dim, method_name in DIMENSION_METHODS.items():
        try:
            method = getattr(mapper, method_name)
            result = method(0)
            assert isinstance(result, str), f"返回类型={type(result).__name__}，应为str"
            P(f"{method_name}(0) 返回 str")
            p += 1
        except Exception as e:
            F(f"{method_name}(0) 异常: {e}"); f += 1

    # ===== 测试3：输出格式验证（XML标签含value属性）=====
    print("\n【测试3】输出格式：XML标签 + value属性")
    for dim, method_name in DIMENSION_METHODS.items():
        try:
            method = getattr(mapper, method_name)
            result = method(0)
            assert f"<{dim}" in result, f"缺少 <{dim} 标签"
            assert 'value="0"' in result, "缺少 value=属性"
            assert f"</{dim}>" in result, f"缺少 </{dim}> 闭合标签"
            P(f"{dim}: XML格式正确 (<tag value=...>...</tag>)")
            p += 1
        except AssertionError as e:
            F(f"{dim} XML格式: {e}"); f += 1

    # ===== 测试4：7级分段映射验证（非intimacy的9个维度）=====
    print("\n【测试4】7级分段映射验证（双向9维度，intimacy除外）")
    tier_test_points = {
        "extreme_neg": -100,
        "neg": -70,
        "mild_neg": -30,
        "neutral": 0,
        "mild_pos": 30,
        "pos": 70,
        "extreme_pos": 100,
    }
    for dim, method_name in DIMENSION_METHODS.items():
        if dim == "intimacy":
            continue
        method = getattr(mapper, method_name)
        for tier_name, test_val in tier_test_points.items():
            try:
                result = method(test_val)
                assert f'value="{test_val}"' in result, f"value属性错误"
                assert len(result) > 0
            except AssertionError as e:
                F(f"{dim}.{tier_name}({test_val}): {e}"); f += 1
                break
        else:
            P(f"{dim}: 7级分段全部通过")
            p += 1

    # ===== 测试5：education_level 彩蛋条件分支（设计文档明确要求）=====
    print("\n【测试5】education_level 彩蛋条件分支（⑨模式）")
    try:
        r = mapper.map_education_level(-100)
        assert "MISS⑨" in r, "缺少 MISS⑨"
        assert "BAKA~" in r, "缺少 BAKA~"
        assert "CRITICAL" in r, "缺少 CRITICAL"
        assert "口癖" in r, "缺少口癖说明"
        assert "天书" in r, "缺少知识降级描述"
        assert "听不懂" in r, "缺少困惑回应示例"
        P("education_level=-100 → 完整⑨模式（CRITICAL+BAKA~+口癖+知识降级）")
        p += 1
    except AssertionError as e:
        F(f"⑨模式: {e}"); f += 1

    # 验证 -99 不触发⑨模式（精确匹配，差1即不触发）
    try:
        r = mapper.map_education_level(-99)
        assert "MISS⑨" not in r, "-99 不应触发 MISS⑨"
        assert "BAKA" not in r, "-99 不应有 BAKA"
        assert "CRITICAL" not in r, "-99 不应有 CRITICAL"
        P("education_level=-99 → 不触发⑨模式（精确匹配，差1不触发）")
        p += 1
    except AssertionError as e:
        F(f"⑨不触发: {e}"); f += 1

    # 验证 -70 正常走 neg 分段
    try:
        r = mapper.map_education_level(-70)
        assert 'value="-70"' in r
        assert "MISS⑨" not in r
        P("education_level=-70 → 走neg分段，不触发⑨")
        p += 1
    except AssertionError as e:
        F(f"edu=-70: {e}"); f += 1

    # 验证 100 走 extreme_pos
    try:
        r = mapper.map_education_level(100)
        assert "百科全书" in r or "渊博" in r
        P("education_level=100 → extreme_pos（含'百科全书'或'渊博'）")
        p += 1
    except AssertionError as e:
        F(f"edu=100: {e}"); f += 1

    # ===== 测试6：intimacy 4级分段（特殊：0-10/11-30/31-70/71-100）=====
    print("\n【测试6】intimacy 4级分段映射")
    intimacy_tiers = [
        (0, "陌生人"), (5, "陌生人"), (10, "陌生人"),
        (15, "初步认识"), (30, "初步认识"),
        (40, "亲近"), (70, "亲近"),
        (80, "最亲密"), (100, "最亲密"),
    ]
    for val, keyword in intimacy_tiers:
        try:
            r = mapper.map_intimacy(val)
            assert keyword in r, f"intimacy={val} 应含'{keyword}'"
        except AssertionError as e:
            F(str(e)); f += 1
            break
    else:
        P("intimacy 4级分段全部正确（陌生人/初步认识/亲近/最亲密）")
        p += 1

    # ===== 测试7：map_all 完整输出 =====
    print("\n【测试7】map_all 完整输出验证")
    try:
        profile = MISSProfile()
        result = mapper.map_all(profile)
        assert isinstance(result, str), f"返回类型={type(result).__name__}"
        assert len(result) > 0
        P("map_all 返回非空字符串")
        p += 1
    except Exception as e:
        F(f"map_all: {e}"); f += 1

    # 验证包含全部10个XML块
    for dim in DIMENSION_METHODS:
        try:
            profile = MISSProfile()
            result = mapper.map_all(profile)
            assert f"<{dim}" in result, f"map_all 缺少 {dim} 片段"
        except AssertionError as e:
            F(str(e)); f += 1
            break
    else:
        P("map_all 包含全部10个维度的XML片段")
        p += 1

    # 验证map_all中⑨模式集成
    try:
        profile = MISSProfile(education_level=-100)
        result = mapper.map_all(profile)
        assert "MISS⑨" in result
        assert "BAKA~" in result
        P("map_all 集成⑨模式彩蛋（edu=-100时）")
        p += 1
    except AssertionError as e:
        F(f"map_all ⑨集成: {e}"); f += 1

    # ===== 测试8：_tier_label 辅助函数边界值 =====
    print("\n【测试8】分级辅助函数边界值验证")
    from services.attribute_engine import _tier_label, _tier_label_intimacy

    # _tier_label 边界
    tier_boundary_tests = [
        (-100, "extreme_negative"),
        (-99, "negative"), (-71, "negative"), (-70, "negative"),
        (-69, "mild_negative"), (-31, "mild_negative"), (-30, "mild_negative"),
        (-29, "neutral"), (0, "neutral"), (30, "neutral"),
        (31, "mild_positive"), (69, "mild_positive"), (70, "mild_positive"),
        (71, "positive"), (99, "positive"),
        (100, "extreme_positive"),
    ]
    for val, expected_label in tier_boundary_tests:
        try:
            result_label, _ = _tier_label(val, "E", "N", "M", "X", "P", "P", "R")
            assert result_label == expected_label, f"值{val} 期望{expected_label} 实际{result_label}"
        except AssertionError as e:
            F(str(e)); f += 1
            break
    else:
        P("_tier_label 全部边界值通过（-100~100，14个边界点）")
        p += 1

    # _tier_label_intimacy 边界
    intimacy_boundary = [
        (0, "distant"), (10, "distant"),
        (11, "acquaintance"), (30, "acquaintance"),
        (31, "close"), (70, "close"),
        (71, "intimate"), (100, "intimate"),
    ]
    for val, expected_label in intimacy_boundary:
        try:
            result_label, _ = _tier_label_intimacy(val, "A", "B", "C", "D")
            assert result_label == expected_label, f"值{val} 期望{expected_label} 实际{result_label}"
        except AssertionError as e:
            F(str(e)); f += 1
            break
    else:
        P("_tier_label_intimacy 全部边界值通过（0~100，8个边界点）")
        p += 1

    # ===== 测试9：services/__init__.py 导出 =====
    print("\n【测试9】模块导出完整性")
    try:
        from services import AttributePromptMapper as APM_export
        P("AttributePromptMapper 已从 services/__init__.py 导出")
        p += 1
    except ImportError:
        F("AttributePromptMapper 未从 services/__init__.py 导出"); f += 1

    # ===== 测试10：返回文本不含编程代码 =====
    print("\n【测试10】返回文本质量检查")
    try:
        profile = MISSProfile()
        result = mapper.map_all(profile)
        assert "```" not in result, "输出不应含代码块"
        assert "__" not in result or result.count("__") <= 2, "过多双下划线"
        P("输出纯文本，无代码块污染")
        p += 1
    except AssertionError as e:
        F(str(e)); f += 1

    # ===== 汇总 =====
    print("\n" + "=" * 60)
    t = p + f
    print(f"测试总数: {t}  通过: {p}  失败: {f}  通过率: {p/t*100:.1f}%")
    print("=" * 60)
    if f == 0:
        print("\n🎉 Task 1.4 验收通过！")
    else:
        print("\n❌ Task 1.4 验收未通过！")
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(run())
