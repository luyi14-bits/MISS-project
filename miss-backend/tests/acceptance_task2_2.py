"""
Task 2.2 严格验收测试 - 提示词组装器（Prompt Builder）
验收标准：调用后返回格式正确的 messages 列表
"""
import sys, os
os.environ["DB_URL"] = "sqlite:///./tests/data/test_acceptance_2_2.db"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Base
from database import engine, SessionLocal
from services.prompt_builder import PromptBuilder
from services.attribute_engine import MISSProfile
from config import config


def P(t): print(f"  ✅ PASS: {t}")
def F(t, d=""): print(f"  ❌ FAIL: {t}"); d and print(f"     {d}")


def seed(sid, msgs):
    from services.memory_manager import ConversationStore
    s = ConversationStore()
    for m in msgs:
        s.add_message(sid, m["role"], m["content"])


def run():
    p = f = 0

    # 初始化测试数据库
    Base.metadata.create_all(bind=engine)

    try:
        print("=" * 60)
        print("Task 2.2 验收测试 - 提示词组装器（Prompt Builder）")
        print("=" * 60)

        # ===== 1. 类结构与初始化 =====
        print("\n【测试1】类结构与组件初始化")
        builder = PromptBuilder()

        try:
            assert hasattr(builder, "_easter_egg_engine"), "缺少 _easter_egg_engine"
            P("EasterEggEngine 已初始化")
            p += 1
        except AssertionError as e: F(str(e)); f += 1

        try:
            assert hasattr(builder, "_cross_effect_calc"), "缺少 _cross_effect_calc"
            P("CrossEffectCalculator 已初始化")
            p += 1
        except AssertionError as e: F(str(e)); f += 1

        try:
            assert hasattr(builder, "_attribute_mapper"), "缺少 _attribute_mapper"
            P("AttributePromptMapper 已初始化")
            p += 1
        except AssertionError as e: F(str(e)); f += 1

        try:
            assert hasattr(builder, "_conversation_store"), "缺少 _conversation_store"
            P("ConversationStore 已初始化")
            p += 1
        except AssertionError as e: F(str(e)); f += 1

        try:
            assert hasattr(builder, "_jinja_env"), "缺少 Jinja2 Environment"
            P("Jinja2 Environment 已初始化")
            p += 1
        except AssertionError as e: F(str(e)); f += 1

        # ===== 2. build 方法签名 =====
        print("\n【测试2】build 方法签名验证")
        import inspect
        sig = inspect.signature(builder.build)
        params = list(sig.parameters.keys())
        expected_params = ["session_id", "user_message", "profile"]
        for ep in expected_params:
            if ep in params: P(f"参数 {ep} 存在"); p += 1
            else: F(f"缺少参数 {ep}"); f += 1

        if sig.return_annotation == list[dict]:
            P("返回类型: list[dict]"); p += 1
        else:
            F(f"返回类型={sig.return_annotation}，期望 list[dict]"); f += 1

        # ===== 3. 核心验收：返回格式 =====
        print("\n【测试3】核心验收：build() 返回正确 messages 列表")
        result = builder.build("test_3", "你好", MISSProfile())

        if isinstance(result, list): P("返回 list"); p += 1
        else: F(f"返回 {type(result).__name__}"); f += 1

        if len(result) >= 2: P(f"长度 >= 2 (system + user): {len(result)}"); p += 1
        else: F(f"长度={len(result)}，期望>=2"); f += 1

        # 每条消息的格式
        for i, msg in enumerate(result):
            if "role" in msg: P(f"[{i}] 含 role 字段"); p += 1
            else: F(f"[{i}] 缺 role"); f += 1
            if "content" in msg: P(f"[{i}] 含 content 字段"); p += 1
            else: F(f"[{i}] 缺 content"); f += 1
            if isinstance(msg["content"], str) and len(msg["content"]) > 0:
                P(f"[{i}] content 为非空str"); p += 1
            else: F(f"[{i}] content 异常"); f += 1
            if msg["role"] in ("system", "user", "assistant"):
                P(f"[{i}] role={msg['role']} 合法"); p += 1
            else: F(f"[{i}] role={msg['role']} 非法"); f += 1

        # ===== 4. system 消息位置与内容 =====
        print("\n【测试4】system 消息（第一条）验证")
        if result[0]["role"] == "system": P("第一条是 system"); p += 1
        else: F(f"第一条是 {result[0]['role']}"); f += 1

        system = result[0]["content"]
        # 必须包含7个核心区块
        required = [
            "system_directive", "persona", "dynamic_state", "knowledge_ceiling",
            "cognitive_engine", "behavioral_constraints", "response_format",
        ]
        for sec in required:
            if f"<{sec}>" in system: P(f"含 <{sec}>"); p += 1
            else: F(f"缺 <{sec}>"); f += 1

        # ===== 5. user 消息位置 =====
        print("\n【测试5】user 消息（最后一条）验证")
        if result[-1]["role"] == "user": P("最后一条是 user"); p += 1
        else: F(f"最后一条是 {result[-1]['role']}"); f += 1

        test_msg = "你今天心情怎么样？"
        result = builder.build("test_5", test_msg, MISSProfile())
        if result[-1]["content"] == test_msg: P("user消息内容一致"); p += 1
        else: F(f"内容={result[-1]['content']}"); f += 1

        # ===== 6. 对话历史集成 =====
        print("\n【测试6】对话历史集成验证")
        sid = "test_hist"
        seed(sid, [
            {"role": "user", "content": "第一轮用户"},
            {"role": "assistant", "content": "第一轮助手"},
            {"role": "user", "content": "第二轮用户"},
            {"role": "assistant", "content": "第二轮助手"},
        ])
        result = builder.build(sid, "第三轮用户", MISSProfile())
        # 应该: system + 4条历史 + new_user = 6条
        if len(result) == 6: P("历史消息数量正确(6)"); p += 1
        else: F(f"期望6条，实际{len(result)}"); f += 1
        if result[1]["content"] == "第一轮用户": P("历史顺序正确-第1条"); p += 1
        else: F("历史顺序错误"); f += 1
        if result[4]["content"] == "第二轮助手": P("历史顺序正确-第4条"); p += 1
        else: F("历史顺序错误"); f += 1

        # ===== 7. 对话窗口限制 =====
        print("\n【测试7】对话窗口限制（config.conversation_window_size）")
        sid2 = "test_window"
        many = []
        for i in range(25):
            many.append({"role": "user", "content": f"Q{i}"})
            many.append({"role": "assistant", "content": f"A{i}"})
        seed(sid2, many)
        result = builder.build(sid2, "最新消息", MISSProfile())
        history_count = len(result) - 2
        if history_count <= config.conversation_window_size:
            P(f"窗口限制生效: history={history_count} <= {config.conversation_window_size}")
            p += 1
        else:
            F(f"窗口超限: {history_count} > {config.conversation_window_size}"); f += 1

        # ===== 8. 空的对话窗口 =====
        print("\n【测试8】空对话窗口（无历史消息）")
        result = builder.build("test_empty_hist", "你好", MISSProfile())
        if len(result) == 2: P("空历史=2条(system+user)"); p += 1
        else: F(f"期望2条，实际{len(result)}"); f += 1

        # ===== 9. ⑨模式端到端集成 =====
        print("\n【测试9】⑨模式端到端集成（edu=-100）")
        profile = MISSProfile(education_level=-100)
        result = builder.build("test_cirno", "什么是宇宙？", profile)
        system = result[0]["content"]
        cirno_checks = [
            ("MISS⑨", "MISS⑨" in system),
            ("BAKA~", "BAKA~" in system),
            ("CRITICAL", "CRITICAL" in system),
            ("easter_egg区块", "<easter_egg>" in system),
            ("knowledge_ceiling含天书", "天书" in system or "听不懂" in system),
            ("角色名无MISS小姐", "MISS小姐" not in system),
        ]
        for desc, ok in cirno_checks:
            if ok: P(desc); p += 1
            else: F(desc); f += 1

        # ===== 10. 交叉影响端到端 =====
        print("\n【测试10】交叉影响端到端集成")
        profile = MISSProfile(education_level=-100, curiosity=100)
        result = builder.build("test_cross", "宇宙有多大？", profile)
        system = result[0]["content"]
        if "好奇笨蛋" in system: P("好奇笨蛋交叉影响注入"); p += 1
        else: F("好奇笨蛋未注入"); f += 1
        if "cross_persona" in system: P("cross_persona区块渲染"); p += 1
        else: F("cross_persona未渲染"); f += 1

        # 不触发交叉影响
        profile2 = MISSProfile()
        result2 = builder.build("test_no_cross", "你好", profile2)
        system2 = result2[0]["content"]
        if "cross_persona" not in system2: P("无交叉影响时不渲染cross_persona"); p += 1
        else: F("无交叉影响了仍渲染cross_persona"); f += 1

        # ===== 11. allowed_domains 集成 =====
        print("\n【测试11】allowed_domains 集成")
        profile = MISSProfile(allowed_domains=["数学", "物理"])
        result = builder.build("test_domains", "给我讲讲", profile)
        system = result[0]["content"]
        if "数学、物理" in system: P("allowed_domains join注入"); p += 1
        else: F("allowed_domains未注入"); f += 1
        if "知识领域限制" in system: P("知识领域限制区块渲染"); p += 1
        else: F("知识领域限制未渲染"); f += 1

        # ===== 12. 10个属性XML全部注入 =====
        print("\n【测试12】全10维属性XML注入验证")
        result = builder.build("test_attrs", "你好", MISSProfile())
        system = result[0]["content"]
        all_attrs = [
            "rational_emotional", "willpower", "independent_submissive",
            "education_level", "intimacy", "curiosity", "humor",
            "aggression", "social_energy", "adventurousness",
        ]
        for attr in all_attrs:
            if f"<{attr}" in system: P(f"{attr} XML块注入"); p += 1
            else: F(f"{attr} XML块缺失"); f += 1

        # ===== 13. OpenAI 兼容格式 =====
        print("\n【测试13】OpenAI API 兼容格式验证")
        result = builder.build("test_openai", "测试", MISSProfile())
        for i, msg in enumerate(result):
            required_keys = {"role", "content"}
            actual_keys = set(msg.keys())
            if required_keys.issubset(actual_keys):
                P(f"[{i}] 含必需字段 role+content")
                p += 1
            else:
                F(f"[{i}] 缺 {required_keys - actual_keys}"); f += 1

            if msg["role"] in ("system", "user", "assistant"):
                P(f"[{i}] role 合法: {msg['role']}")
                p += 1
            else: F(f"[{i}] role 非法"); f += 1

        # ===== 14. 不同 session_id 隔离 =====
        print("\n【测试14】不同 session_id 对话隔离")
        result_a = builder.build("sess_a", "消息A", MISSProfile())
        result_b = builder.build("sess_b", "消息B", MISSProfile())
        if len(result_a) == 2 and len(result_b) == 2:
            P("空对话session隔离正确(2条)")
            p += 1
        else: F("session隔离异常"); f += 1

        # ===== 15. services/__init__.py 导出 =====
        print("\n【测试15】模块导出完整性")
        try:
            from services import PromptBuilder as PB
            P("PromptBuilder 已从 services/__init__.py 导出")
            p += 1
        except ImportError:
            F("PromptBuilder 未导出"); f += 1

        # ===== 汇总 =====
        print("\n" + "=" * 60)
        t = p + f
        print(f"测试总数: {t}  通过: {p}  失败: {f}  通过率: {p/t*100:.1f}%")
        print("=" * 60)
        if f == 0: print("\n🎉 Task 2.2 验收通过！")
        else: print("\n❌ Task 2.2 验收未通过！")

    finally:
        Base.metadata.drop_all(bind=engine)
        try: os.remove("tests/data/test_acceptance_2_2.db")
        except OSError: pass

    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(run())
