# Copyright (C) 2026  MISS Project Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
"""
Task 2.1 严格验收测试 - MISS小姐 Jinja2 系统提示词模板
验收标准：传入 profile 输出完整提示词，education_level=-100 时自动含⑨和BAKA
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jinja2 import Environment, FileSystemLoader
from services.attribute_engine import MISSProfile, EasterEggEngine, CrossEffectCalculator


def P(test): print(f"  ✅ PASS: {test}")
def F(test, d=""): print(f"  ❌ FAIL: {test}"); d and print(f"     {d}")


TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")


def render(profile=None, eggs=None, cross_effects=None, attribute_xml="", memories=None):
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    tpl = env.get_template("miss_system.j2")
    return tpl.render(
        profile=profile or MISSProfile(),
        eggs=eggs or {},
        cross_effects=cross_effects or [],
        attribute_xml=attribute_xml,
        memories=memories or [],
    )


def run():
    p = f = 0
    print("=" * 60)
    print("Task 2.1 验收测试 - Jinja2 系统提示词模板")
    print("=" * 60)

    # ===== 1. 模板文件存在性 =====
    print("\n【测试1】模板文件存在且可加载")
    try:
        fn = os.path.join(TEMPLATE_DIR, "miss_system.j2")
        assert os.path.exists(fn), "文件不存在"
        env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
        tpl = env.get_template("miss_system.j2")
        P("miss_system.j2 存在且 Jinja2 可加载")
        p += 1
    except Exception as e:
        F(str(e)); f += 1

    # ===== 2. 设计文档要求的8个XML区块 =====
    print("\n【测试2】设计文档要求的8个必需区块")
    REQUIRED_BLOCKS = [
        "system_directive",
        "persona",
        "dynamic_state",
        "knowledge_ceiling",
        "easter_egg",     # 条件渲染，模板中需存在该标签代码
        "cognitive_engine",
        "behavioral_constraints",
        "response_format",
    ]
    # 读取原始模板文本
    with open(fn, "r", encoding="utf-8") as fh:
        raw = fh.read()

    for block in REQUIRED_BLOCKS:
        tag = f"<{block}>"
        if tag in raw:
            P(f"模板含 {tag}")
            p += 1
        else:
            F(f"模板缺 {tag}"); f += 1

    # ===== 3. 默认渲染输出完整性 =====
    print("\n【测试3】默认渲染（默认profile, 无彩蛋, 无记忆）")
    result = render()
    always_blocks = [
        "system_directive", "persona", "dynamic_state",
        "knowledge_ceiling", "cognitive_engine",
        "behavioral_constraints", "response_format",
    ]
    for block in always_blocks:
        if f"<{block}>" in result:
            P(f"渲染后含 <{block}>")
            p += 1
        else:
            F(f"渲染后缺 <{block}>"); f += 1

    # easter_egg 默认不渲染
    if "<easter_egg>" not in result:
        P("无彩蛋时不渲染 <easter_egg>（正确）")
        p += 1
    else:
        F("无彩蛋时不应渲染 <easter_egg>"); f += 1

    # recalled_memories 默认不渲染
    if "recalled_memories" not in result.lower():
        P("无记忆时不渲染 recalled_memories（正确）")
        p += 1
    else:
        F("无记忆时不应渲染 recalled_memories"); f += 1

    # ===== 4. 核心验收：edu=-100 + cirno 彩蛋 =====
    print("\n【测试4】核心验收：education_level=-100 → ⑨ + BAKA")
    profile = MISSProfile(education_level=-100)
    eggs = EasterEggEngine().evaluate(profile)
    result = render(profile=profile, eggs=eggs,
                    attribute_xml='<education_level value="-100">MISS⑨</education_level>')

    checks = [
        ("角色名含 MISS⑨", "MISS⑨" in result),
        ("角色名不含 MISS小姐", "MISS小姐" not in result),
        ("口癖 BAKA~", "BAKA~" in result),
        ("CRITICAL 警告", "CRITICAL" in result),
        ("easter_egg 区块", "<easter_egg>" in result),
        ("冰蓝色 name_color", "#00BFFF" in result),
        ("冰晶翅膀 avatar_decor", "ice_crystal_wings" in result),
        ("知识降级规则", "天书" in result or "听不懂" in result),
        ("inner_thought 字段", "inner_thought" in result),
        ("spoken 字段", "spoken" in result),
        ("Track A", "Track A" in result),
        ("Track B", "Track B" in result),
    ]
    for desc, ok in checks:
        if ok: P(desc); p += 1
        else: F(desc); f += 1

    # ===== 5. 默认 profile（无彩蛋）验证 =====
    print("\n【测试5】默认 profile（education_level=0）→ MISS小姐")
    result2 = render()
    checks2 = [
        ("角色名 MISS小姐", "MISS小姐" in result2),
        ("不含 MISS⑨", "MISS⑨" not in result2),
        ("不含 BAKA", "BAKA~" not in result2),
        ("不含 CRITICAL", "CRITICAL" not in result2),
    ]
    for desc, ok in checks2:
        if ok: P(desc); p += 1
        else: F(desc); f += 1

    # ===== 6. attribute_xml 注入 =====
    print("\n【测试6】attribute_xml 变量注入")
    xml = '<willpower value="100">钢铁</willpower>\n<curiosity value="-100">无兴趣</curiosity>'
    r = render(attribute_xml=xml)
    if '<willpower value="100">钢铁</willpower>' in r: P("willpower XML注入"); p += 1
    else: F("willpower XML未注入"); f += 1
    if '<curiosity value="-100">无兴趣</curiosity>' in r: P("curiosity XML注入"); p += 1
    else: F("curiosity XML未注入"); f += 1

    # ===== 7. cross_effects 注入 =====
    print("\n【测试7】cross_effects 列表注入")
    effects = CrossEffectCalculator().calculate(
        MISSProfile(education_level=-100, curiosity=100)
    )
    r = render(
        profile=MISSProfile(education_level=-100, curiosity=100),
        cross_effects=effects,
    )
    if "好奇笨蛋" in r: P("cross_effects 名称注入"); p += 1
    else: F("cross_effects 名称未注入"); f += 1
    if "cross_persona" in r: P("cross_persona 区块渲染"); p += 1
    else: F("cross_persona 区块未渲染"); f += 1
    if "amplify" in r or "conflict" in r: P("cross_effects type 注入"); p += 1
    else: F("cross_effects type 未注入"); f += 1

    # 无 cross_effects 时不渲染
    r2 = render()
    if "cross_persona" not in r2: P("无cross_effects时不渲染cross_persona"); p += 1
    else: F("无cross_effects时不应渲染cross_persona"); f += 1

    # ===== 8. memories 注入 =====
    print("\n【测试8】memories 列表注入")
    mems = [
        {"importance": 90, "category": "emotional", "content": "用户昨天分享了童年回忆。"},
        {"importance": 70, "category": "event", "content": "上周一起去过游乐园。"},
    ]
    r = render(memories=mems)
    if "童年回忆" in r: P("memory 内容注入"); p += 1
    else: F("memory 内容未注入"); f += 1
    if "游乐园" in r: P("多条 memory 同时注入"); p += 1
    else: F("多条 memory 注入失败"); f += 1
    if "90" in r and "70" in r: P("importance 值注入"); p += 1
    else: F("importance 未注入"); f += 1
    if "emotional" in r: P("category 注入"); p += 1
    else: F("category 未注入"); f += 1

    # 无 memories 时不渲染
    r2 = render()
    if "recalled_memories" not in r2.lower(): P("无memories时不渲染"); p += 1
    else: F("无memories时应不渲染"); f += 1

    # ===== 9. allowed_domains 条件渲染 =====
    print("\n【测试9】allowed_domains 条件渲染")
    pf = MISSProfile(allowed_domains=["艺术", "人文", "科学"])
    r = render(profile=pf)
    if "艺术、人文、科学" in r: P("allowed_domains join渲染"); p += 1
    else: F("allowed_domains 未正确join"); f += 1
    if "知识领域限制" in r: P("知识领域限制区块渲染"); p += 1
    else: F("知识领域限制区块未渲染"); f += 1

    pf2 = MISSProfile(allowed_domains=[])
    r2 = render(profile=pf2)
    if "知识领域限制" not in r2: P("allowed_domains空时不渲染限制"); p += 1
    else: F("allowed_domains空时不应渲染限制"); f += 1

    # ===== 10. knowledge_ceiling 教育水平分层 =====
    print("\n【测试10】knowledge_ceiling 教育水平分层渲染")
    # edu=-100 → CRITICAL + 天书 + 知识降级
    r = render(profile=MISSProfile(education_level=-100))
    if "CRITICAL" in r and "天书" in r: P("edu=-100 → CRITICAL + 知识降级"); p += 1
    else: F("edu=-100 知识天花板不完整"); f += 1

    # edu=-70 → 不触发⑨CRITICAL但仍有降级
    r = render(profile=MISSProfile(education_level=-70))
    if "基础层面" in r: P("edu=-70 → 基础层面描述"); p += 1
    else: F("edu=-70 描述缺失"); f += 1

    # edu=0 → 普通
    r = render(profile=MISSProfile(education_level=0))
    if "普通的知识储备" in r or "日常常识" in r: P("edu=0 → 普通知识储备"); p += 1
    else: F("edu=0 描述缺失"); f += 1

    # edu=100 → 丰富
    r = render(profile=MISSProfile(education_level=100))
    if "丰富" in r: P("edu=100 → 丰富知识"); p += 1
    else: F("edu=100 描述缺失"); f += 1

    # ===== 11. response_format JSON 双轨 =====
    print("\n【测试11】response_format JSON 双轨输出模板")
    r = render()
    checks = [
        ("含 inner_thought 键", '"inner_thought"' in r),
        ("含 spoken 键", '"spoken"' in r),
        ("JSON 格式标记", 'json' in r.lower()),
        ("双大括号正确（非JSON括号）", '{\n  "inner_thought"' in r or '{\n  "inner_thought"' in r.replace(' ', '')),
    ]
    for desc, ok in checks:
        if ok: P(desc); p += 1
        else: F(desc); f += 1

    # ===== 12. behavioral_constraints 10条 =====
    print("\n【测试12】behavioral_constraints 反面约束")
    r = render()
    constraints_keywords = [
        "不要破坏角色一致性", "不要过度迎合", "不要空洞地说教",
        "不要过度使用RP格式", "不要让回复过长",
        "不要输出任何编程代码",
        "不要在 inner_thought 中欺骗",
    ]
    for kw in constraints_keywords:
        if kw in r: P(f"约束: {kw}"); p += 1
        else: F(f"缺约束: {kw}"); f += 1

    # ===== 13. cognitive_engine 决策树 =====
    print("\n【测试13】cognitive_engine 决策树完整性")
    r = render()
    decision_keywords = [
        "Track A", "Track B", "inner_thought", "spoken",
        "决策树", "IF 亲密度", "IF 教育水平",
        "IF 好奇心", "IF 攻击性", "IF 意志力",
    ]
    for kw in decision_keywords:
        if kw in r: P(f"决策树含: {kw}"); p += 1
        else: F(f"决策树缺: {kw}"); f += 1

    # ===== 14. 模板无语法错误 =====
    print("\n【测试14】模板无 Jinja2 语法错误")
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    try:
        tpl = env.get_template("miss_system.j2")
        # 测试各种极端组合
        tpl.render(profile=MISSProfile(), eggs={}, cross_effects=[], attribute_xml="", memories=[])
        tpl.render(profile=MISSProfile(education_level=-100),
                   eggs={"cirno_mode": {"catchphrase": "BAKA~", "name_color": "#00BFFF",
                       "avatar_decor": "ice_crystal_wings", "wrong_answer_probability": 0.30,
                       "knowledge_fallback": "simple_confusion"}},
                   cross_effects=[{"persona_name": "X", "type": "amplify", "effect": "Y"}],
                   attribute_xml="<test>OK</test>",
                   memories=[{"importance": 1, "category": "test", "content": "test"}])
        P("极端参数组合渲染无语法错误")
        p += 1
    except Exception as e:
        F(f"渲染异常: {e}"); f += 1

    # ===== 15. 教育水平= -99 不触发⑨模式 =====
    print("\n【测试15】education_level=-99 精确不触发⑨")
    profile = MISSProfile(education_level=-99)
    eggs = EasterEggEngine().evaluate(profile)
    r = render(profile=profile, eggs=eggs)
    if "MISS⑨" not in r: P("-99 → 不含 MISS⑨（精确匹配）"); p += 1
    else: F("-99 → 错误触发 MISS⑨"); f += 1
    if "CRITICAL" in r: P("-99 → 仍含 CRITICAL（教育低）"); p += 1
    else: F("-99 → 缺 CRITICAL"); f += 1

    # ===== 汇总 =====
    print("\n" + "=" * 60)
    t = p + f
    print(f"测试总数: {t}  通过: {p}  失败: {f}  通过率: {p/t*100:.1f}%")
    print("=" * 60)
    if f == 0: print("\n🎉 Task 2.1 验收通过！")
    else: print("\n❌ Task 2.1 验收未通过！")
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(run())
