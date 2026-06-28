"""
Task 1.3 严格验收测试 - 属性交叉影响计算器
验收标准：给定 profile 返回正确的交叉人格 + 对应的提示词追加文本
同时验证程序组是否严格按照设计文档实现
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.attribute_engine import MISSProfile, CrossEffectCalculator, CROSS_EFFECTS


def P(test): print(f"  ✅ PASS: {test}")
def F(test, d=""): print(f"  ❌ FAIL: {test}"); d and print(f"     {d}")


def run():
    p = f = 0
    calc = CrossEffectCalculator()
    print("=" * 60)
    print("Task 1.3 验收测试 - 属性交叉影响计算器")
    print("=" * 60)

    # === 1. 程序组规范性：设计文档中要求的数据结构验证 ===
    print("\n【测试1】程序组规范性 - 设计文档要求的结构字段")
    # 设计文档要求的5个核心字段
    required_keys = {"conditions", "type", "persona_name", "effect", "trigger_threshold"}
    extra_allowed = {"id"}  # id 是程序组额外加的

    for i, rule in enumerate(CROSS_EFFECTS):
        actual_keys = set(rule.keys())

        # 设计要求的字段必须全有
        missing = required_keys - actual_keys
        if missing:
            F(f"CROSS_EFFECTS[{i}] 缺少设计文档要求字段: {missing}")
            f += 1
        else:
            P(f"CROSS_EFFECTS[{i}] ({rule.get('id','?')}) 5个设计字段齐全")
            p += 1

        # 检查是否有不允许的陌生字段
        unknown = actual_keys - required_keys - extra_allowed
        if unknown:
            F(f"CROSS_EFFECTS[{i}] 包含未定义字段: {unknown}")
            f += 1
        else:
            P(f"CROSS_EFFECTS[{i}] 无多余字段")
            p += 1

        # 验证 conditions 结构
        conds = rule["conditions"]
        if isinstance(conds, dict) and len(conds) == 2:
            P(f"CROSS_EFFECTS[{i}] conditions 包含2个属性=2")
            p += 1
        else:
            F(f"CROSS_EFFECTS[{i}] conditions 结构异常: {conds}")
            f += 1

        # 验证 trigger_threshold 结构
        tt = rule["trigger_threshold"]
        if isinstance(tt, dict) and len(tt) == 2:
            P(f"CROSS_EFFECTS[{i}] trigger_threshold 包含2个阈值=2")
            p += 1
        else:
            F(f"CROSS_EFFECTS[{i}] trigger_threshold 结构异常: {tt}")
            f += 1

    # === 2. 10组交叉影响完整性 ===
    print("\n【测试2】10组交叉影响完整性")
    expected_ids = {
        "curious_baka", "tsundere_lover", "dramatic_comedian",
        "volatile_heiress", "lone_adventurer", "scholarly_bore",
        "clingy_koala", "ice_queen", "party_animal", "relentless_warrior",
    }
    actual_ids = {r["id"] for r in CROSS_EFFECTS}

    if len(CROSS_EFFECTS) != 10:
        F(f"总数={len(CROSS_EFFECTS)}, 设计文档要求10组")
        f += 1
    else:
        P("总计 10 组交叉影响（与设计文档一致）")
        p += 1

    missing_ids = expected_ids - actual_ids
    if missing_ids:
        for mid in missing_ids:
            F(f"缺失: {mid}")
            f += 1
    else:
        P("10个交叉人格id完整齐全")
        p += 1

    extra_ids = actual_ids - expected_ids
    if extra_ids:
        for eid in extra_ids:
            F(f"多出未知id: {eid}")
            f += 1
    else:
        P("无多余id")
        p += 1

    # === 3. 设计文档明确列出的2组必须精确匹配 ===
    print("\n【测试3】设计文档明确要求的2组交叉影响精确匹配")

    # 第一组：好奇笨蛋
    r0 = CROSS_EFFECTS[0]
    checks = [
        ("id", "curious_baka"),
        ("conditions", {"education_level": -100, "curiosity": 100}),
        ("type", "amplify"),
        ("persona_name", "好奇笨蛋"),
        ("trigger_threshold", {"education_level": -90, "curiosity": 90}),
    ]
    for key, expected in checks:
        if r0[key] == expected:
            P(f"好奇笨蛋.{key} = {expected}")
            p += 1
        else:
            F(f"好奇笨蛋.{key} 期望={expected}, 实际={r0[key]}")
            f += 1
    # effect 不要求逐字，但必须包含关键描述
    if "理解力有限" in r0["effect"]:
        P("好奇笨蛋.effect 包含关键描述'理解力有限'")
        p += 1
    else:
        F("好奇笨蛋.effect 缺少关键描述")
        f += 1

    # 第二组：傲娇恋人
    r1 = CROSS_EFFECTS[1]
    checks2 = [
        ("id", "tsundere_lover"),
        ("conditions", {"independent_submissive": -100, "intimacy": 100}),
        ("type", "conflict"),
        ("persona_name", "傲娇恋人"),
    ]
    for key, expected in checks2:
        if r1[key] == expected:
            P(f"傲娇恋人.{key} = {expected}")
            p += 1
        else:
            F(f"傲娇恋人.{key} 期望={expected}, 实际={r1[key]}")
            f += 1
    # 设计文档中傲娇恋人没有 trigger_threshold，但程序组补充了
    if "trigger_threshold" in r1:
        P("傲娇恋人.trigger_threshold 存在（程序组补充，可接受）")
        p += 1

    if "推开对方" in r1["effect"] or "傲娇" in r1["effect"]:
        P("傲娇恋人.effect 包含推拉式行为指导")
        p += 1
    else:
        F("傲娇恋人.effect 缺少关键描述")
        f += 1

    # === 4. 全部10组逐一触发测试 ===
    print("\n【测试4】全部10组逐一触发测试")
    test_cases = [
        ("curious_baka", "好奇笨蛋", {"education_level": -100, "curiosity": 100}),
        ("tsundere_lover", "傲娇恋人", {"independent_submissive": -100, "intimacy": 100}),
        ("dramatic_comedian", "感性喜剧人", {"rational_emotional": 100, "humor": 100}),
        ("volatile_heiress", "暴走千金", {"aggression": 100, "willpower": -100}),
        ("lone_adventurer", "孤胆冒险家", {"social_energy": -100, "adventurousness": 100}),
        ("scholarly_bore", "书呆子", {"education_level": 100, "curiosity": -100}),
        ("clingy_koala", "黏人精", {"intimacy": 100, "independent_submissive": 100}),
        ("ice_queen", "冰山美人", {"rational_emotional": -100, "aggression": -100}),
        ("party_animal", "派对狂人", {"social_energy": 100, "adventurousness": 100}),
        ("relentless_warrior", "钢铁战士", {"willpower": 100, "aggression": 100}),
    ]
    for eid, ename, kwargs in test_cases:
        try:
            profile = MISSProfile(**kwargs)
            effects = calc.calculate(profile)
            matched = [e for e in effects if e["id"] == eid]
            if len(matched) == 1:
                if matched[0]["persona_name"] == ename:
                    P(f"{ename}({eid}) 正确触发，persona_name匹配")
                    p += 1
                else:
                    F(f"{eid} persona_name不匹配: {matched[0]['persona_name']}")
                    f += 1
            else:
                F(f"{eid} 应触发1次，实际{len(matched)}次")
                f += 1
        except Exception as e:
            F(f"{eid} 触发异常: {e}")
            f += 1

    # === 5. 精确匹配验证（差1也不行）===
    print("\n【测试5】精确匹配验证：差1不触发")
    near_miss_cases = [
        ("curious_baka一个条件差1", {"education_level": -99, "curiosity": 100}),
        ("curious_baka另一个差1", {"education_level": -100, "curiosity": 99}),
        ("tsundere_lover差1", {"independent_submissive": -99, "intimacy": 100}),
        ("dramatic_comedian差1", {"rational_emotional": 99, "humor": 100}),
    ]
    for desc, kwargs in near_miss_cases:
        try:
            profile = MISSProfile(**kwargs)
            effects = calc.calculate(profile)
            eids = {e["id"] for e in effects}
            # 应该不包含任何已知的交叉人格
            unrelated = eids & expected_ids
            if not unrelated:
                P(f"{desc} → 正确不触发任何交叉人格")
                p += 1
            else:
                F(f"{desc} → 不应触发但触发了: {unrelated}")
                f += 1
        except Exception as e:
            F(f"{desc} 异常: {e}")
            f += 1

    # === 6. 返回类型和结构 ===
    print("\n【测试6】返回类型和结构验证")
    try:
        profile = MISSProfile(education_level=-100, curiosity=100)
        effects = calc.calculate(profile)

        if isinstance(effects, list):
            P("返回类型为 list")
            p += 1
        else:
            F(f"返回类型错误: {type(effects).__name__}")
            f += 1

        for e in effects:
            for required_field in ["id", "type", "persona_name", "effect"]:
                if required_field in e and isinstance(e[required_field], str) and e[required_field]:
                    pass
                else:
                    F(f"effect[{e.get('id','?')}] 缺少或空字段: {required_field}")
                    f += 1
            P(f"effect[{e['id']}] 4个必需字段完整且非空")
            p += 1
    except Exception as e:
        F(f"结构验证异常: {e}")
        f += 1

    # === 7. 不支持触发场景（空profile、非极端值）===
    print("\n【测试7】不支持触发场景验证")
    non_trigger_profiles = [
        ("全默认0", {}),
        ("单属性非极端", {"education_level": -99}),
        ("所有属性中间值", {k: 50 for k in [
            "rational_emotional","willpower","independent_submissive",
            "education_level","curiosity","humor","aggression",
            "social_energy","adventurousness"
        ]}),
    ]
    for desc, kwargs in non_trigger_profiles:
        try:
            profile = MISSProfile(**kwargs)
            effects = calc.calculate(profile)
            if effects == []:
                P(f"{desc} → 返回空列表（预期）")
                p += 1
            else:
                F(f"{desc} → 应返回空列表，实际{effects}")
                f += 1
        except Exception as e:
            F(f"{desc} 异常: {e}")
            f += 1

    # === 8. 多组合触发 ===
    print("\n【测试8】多组合触发验证")
    profile = MISSProfile(
        education_level=-100, curiosity=100,   # curious_baka
        social_energy=100, adventurousness=100, # party_animal
        willpower=100, aggression=100,          # relentless_warrior
    )
    effects = calc.calculate(profile)
    eids = {e["id"] for e in effects}
    expected_multi = {"curious_baka", "party_animal", "relentless_warrior"}
    if eids == expected_multi:
        P("3个交叉人格同时触发，结果正确")
        p += 1
    else:
        F(f"期望{expected_multi}, 实际{eids}")
        f += 1

    # 不重叠验证
    other = MISSProfile(education_level=-100, curiosity=100, social_energy=100, adventurousness=100)
    effects2 = calc.calculate(other)
    eids2 = {e["id"] for e in effects2}
    expected2 = {"curious_baka", "party_animal"}
    if eids2 == expected2:
        P("2组并发触发，不互相干扰")
        p += 1
    else:
        F(f"期望{expected2}, 实际{eids2}")
        f += 1

    # === 9. services/__init__.py 导出检查 ===
    print("\n【测试9】模块导出检查（延续1.2验收要求）")
    try:
        from services import CrossEffectCalculator as C
        P("CrossEffectCalculator 已从 services/__init__.py 导出")
        p += 1
    except ImportError:
        F("CrossEffectCalculator 未从 services/__init__.py 导出",
          "应添加: from .attribute_engine import CrossEffectCalculator")
        f += 1

    try:
        from services import EasterEggEngine
        P("EasterEggEngine 已从 services/__init__.py 导出（1.2问题已修复）")
        p += 1
    except ImportError:
        F("EasterEggEngine 仍在 services/__init__.py 缺失（1.2问题未修复）")
        f += 1

    # === 汇总 ===
    print("\n" + "=" * 60)
    t = p + f
    print(f"测试总数: {t}  通过: {p}  失败: {f}  通过率: {p/t*100:.1f}%")
    print("=" * 60)
    if f == 0:
        print("\n🎉 Task 1.3 验收通过！")
    else:
        print("\n❌ Task 1.3 验收未通过！")
    return 0 if f == 0 else 1

if __name__ == "__main__":
    sys.exit(run())
