# Copyright (C) 2026  MISS Project Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
"""
Task 4.2 严格验收测试 - 记忆重要性评分 + 摘要生成 (v2: 关键词引擎版)
验收标准: 长时间对话后自动触发评分与压缩
"""
import json, os, sys, uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["DB_URL"] = "sqlite:///./tests/data/test_accept_4_2.db"
os.environ["OPENAI_API_KEY"] = ""

from models import Base
from database import engine, SessionLocal
from models.memory import MemoryEntry
from services.memory_scorer import MemoryScorer
from services.memory_summarizer import MemorySummarizer


def P(t): print(f"  ✅ PASS: {t}")
def F(t, d=""): print(f"  ❌ FAIL: {t}"); d and print(f"     {d}")


def run():
    p = f = 0
    Base.metadata.create_all(bind=engine)

    try:
        print("=" * 65)
        print("Task 4.2 验收测试 - 记忆重要性评分 + 摘要生成 (v2)")
        print("=" * 65)

        scorer = MemoryScorer()
        summarizer = MemorySummarizer()

        # ===== 1. MemoryScorer 无参构造 + 方法签名 =====
        print("\n【测试1】MemoryScorer 类结构")
        import inspect
        for method_name in ["score", "_classify"]:
            if hasattr(scorer, method_name): P(f"含方法: {method_name}"); p += 1
            else: F(f"缺方法: {method_name}"); f += 1

        sig = inspect.signature(scorer.score)
        if "overflow_messages" in sig.parameters: P("score()签名含 overflow_messages 参数"); p += 1
        else: F("score()签名错误"); f += 1
        if "list[dict]" in str(sig.return_annotation): P("score()返回 list[dict]"); p += 1
        else: F(f"返回值={sig.return_annotation}"); f += 1

        # ===== 2. MemoryScorer.score 基本评分 =====
        print("\n【测试2】MemoryScorer.score 基本评分")
        msgs = [
            {"content": "你好", "role": "user", "id": "m1"},
        ]
        result = scorer.score(msgs)
        if len(result) == 1: P("1条入 → 1条出"); p += 1
        else: F(f"len={len(result)}"); f += 1
        if "content" in result[0]: P("结果含 content"); p += 1
        else: F("缺content"); f += 1
        if "importance" in result[0]: P("结果含 importance"); p += 1
        else: F("缺importance"); f += 1
        if "category" in result[0]: P("结果含 category"); p += 1
        else: F("缺category"); f += 1
        if "role" in result[0]: P("结果含 role"); p += 1
        else: F("缺role"); f += 1
        if "id" in result[0]: P("结果含 id"); p += 1
        else: F("缺id"); f += 1
        if 0 <= result[0]["importance"] <= 100: P("importance在0-100范围"); p += 1
        else: F(f"importance={result[0]['importance']}"); f += 1

        # ===== 3. MemoryScorer 空列表 =====
        print("\n【测试3】MemoryScorer.score 空列表")
        result = scorer.score([])
        if result == []: P("空列表 → 返回[]"); p += 1
        else: F(f"len={len(result)}"); f += 1

        # ===== 4. MemoryScorer 自动分类 =====
        print("\n【测试4】MemoryScorer._classify 自动分类")
        classify_tests = [
            ("今天我很开心", "emotional"),
            ("我去超市买了东西", "event"),
            ("Python是一种编程语言", "fact"),
            ("我决定学习新技能", "fact"),  # "决定"不在EVENT_VERBS（含"决定了"但不含"决定"），无事件动词→fact
        ]
        for content, expected in classify_tests:
            cat = scorer._classify(content)
            if cat == expected: P(f"'{content[:15]}...' → {expected}"); p += 1
            else: F(f"'{content[:15]}...' 期望={expected} 实际={cat}"); f += 1

        # ===== 5. MemoryScorer 关键词提升 importance =====
        print("\n【测试5】MemoryScorer 关键词对 importance 的提升")
        plain = scorer.score([{"content": "ok", "role": "user", "id": "x"}])
        rich  = scorer.score([{"content": "我是张三，我喜欢编程，我决定换工作", "role": "user", "id": "y"}])
        if rich[0]["importance"] > plain[0]["importance"]:
            P(f"关键词rich={rich[0]['importance']} > plain={plain[0]['importance']}")
            p += 1
        else: F(f"rich={rich[0]['importance']} plain={plain[0]['importance']}"); f += 1

        # ===== 6. MemoryScorer 感叹号/问号 提升 importance =====
        print("\n【测试6】MemoryScorer 标点符号密度提升 importance")
        emotional_msg = scorer.score([{"content": "太棒了！！！真的很开心！！！", "role": "user", "id": "e"}])
        normal_msg   = scorer.score([{"content": "太棒了真的很开心", "role": "user", "id": "n"}])
        if emotional_msg[0]["importance"] > normal_msg[0]["importance"]:
            P(f"emotional={emotional_msg[0]['importance']} > normal={normal_msg[0]['importance']}")
            p += 1
        else: F(f"e={emotional_msg[0]['importance']} n={normal_msg[0]['importance']}"); f += 1

        # ===== 7. MemorySummarizer 结构 =====
        print("\n【测试7】MemorySummarizer 类结构")
        for method_name in ["process", "_extract_summary", "_save_memory"]:
            if hasattr(summarizer, method_name): P(f"含方法: {method_name}"); p += 1
            else: F(f"缺方法: {method_name}"); f += 1

        sig = inspect.signature(summarizer.process)
        if "session_id" in sig.parameters and "scored_results" in sig.parameters:
            P("process()含 session_id + scored_results"); p += 1
        else: F("process()签名错误"); f += 1

        # ===== 8. 三级分级：高保留 =====
        print("\n【测试8】三级分级：importance≥80 → 保留原文")
        scored = [{"content": "用户花生过敏", "importance": 85, "category": "fact"}]
        result = summarizer.process("s_high", scored)
        if result["retained"] == 1: P("retained=1"); p += 1
        else: F(f"retained={result['retained']}"); f += 1
        db = SessionLocal()
        try:
            entry = db.query(MemoryEntry).filter(MemoryEntry.session_id == "s_high").first()
            if entry and entry.content == "用户花生过敏": P("DB原文保留"); p += 1
            else: F(f"DB={entry.content if entry else 'None'}"); f += 1
        finally: db.close()

        # ===== 9. 三级分级：低丢弃 =====
        print("\n【测试9】三级分级：importance<40 → 丢弃")
        scored = [{"content": "hi", "importance": 5, "category": "event"}]
        result = summarizer.process("s_low", scored)
        if result["discarded"] == 1: P("discarded=1"); p += 1
        else: F(f"discarded={result['discarded']}"); f += 1
        db = SessionLocal()
        try:
            count = db.query(MemoryEntry).filter(MemoryEntry.session_id == "s_low").count()
            if count == 0: P("DB未写入"); p += 1
            else: F(f"count={count}"); f += 1
        finally: db.close()

        # ===== 10. 三级分级：中摘要 =====
        print("\n【测试10】三级分级：40≤importance<80 → 摘要")
        scored = [{"content": "用户说他今天去了一家很不错的咖啡馆，那里的手冲咖啡很棒", "importance": 60, "category": "event"}]
        result = summarizer.process("s_mid", scored)
        if result["summarized"] == 1: P("summarized=1"); p += 1
        else: F(f"summarized={result['summarized']}"); f += 1
        db = SessionLocal()
        try:
            entry = db.query(MemoryEntry).filter(MemoryEntry.session_id == "s_mid").first()
            if entry: P("DB已写入摘要"); p += 1
            else: F("DB未写入"); f += 1
            # 摘要应短于原文
            if entry and len(entry.content) <= len("用户说他今天去了一家很不错的咖啡馆，那里的手冲咖啡很棒"):
                P("摘要长度 ≤ 原文"); p += 1
            else: F(f"摘要len={len(entry.content) if entry else 0}"); f += 1
        finally: db.close()

        # ===== 11. 混合三级 =====
        print("\n【测试11】混合三级处理")
        scored = [
            {"content": "关键信息", "importance": 90, "category": "fact"},
            {"content": "一般聊天内容天气不错", "importance": 55, "category": "event"},
            {"content": "ok", "importance": 10, "category": "event"},
        ]
        result = summarizer.process("s_mix", scored)
        if result == {"retained": 1, "summarized": 1, "discarded": 1}:
            P("retained=1 summarized=1 discarded=1"); p += 1
        else: F(f"result={result}"); f += 1

        # ===== 12. _extract_summary 短内容直返 =====
        print("\n【测试12】_extract_summary 短内容直返")
        short = "今天天气不错"
        result = summarizer._extract_summary(short)
        if result == short: P(f"≤50字直返: {short}"); p += 1
        else: F(f"返回={result}"); f += 1

        # ===== 13. _extract_summary 短内容直返（≤50字不截断）=====
        print("\n【测试13】_extract_summary 短内容直返（≤50字）")
        short2 = "今天天气很不错阳光很好。下午我们去公园散步了"
        result = summarizer._extract_summary(short2)
        # ≤50字 → 直返原文
        if result == short2: P(f"≤50字直返: {short2}"); p += 1
        else: F(f"返回={result}"); f += 1

        # ===== 14. _extract_summary 超长按标点截断 =====
        print("\n【测试14】_extract_summary 超长按标点截断")
        # >50字且有句号且句号在10-50位置 → 在句号处截断
        long_with_punc = "今天的天气真是太好了阳光明媚万里无云空气清新" * 2 + "。然后后面还有更多内容在这里"
        # 总长度约58字，第一段约52字，句号位置约52
        result = summarizer._extract_summary(long_with_punc)
        if "。" in result and len(result) < len(long_with_punc):
            P(f">50字有标点: 在句号处截断, len(result)={len(result)} vs original={len(long_with_punc)}")
            p += 1
        elif len(result) <= 53:
            # 如果标点位置不在10-50范围 → 走 content[:50]+"..."
            P(f">50字有标点但不在10-50范围: 50字截断, len={len(result)}")
            p += 1
        else:
            F(f"返回={result}"); f += 1

        # ===== 15. _save_memory DB写入 =====
        print("\n【测试15】_save_memory DB写入")
        summarizer._save_memory("s_db", "test memory", 77, "emotional")
        db = SessionLocal()
        try:
            entry = db.query(MemoryEntry).filter(MemoryEntry.session_id == "s_db").first()
            if entry: P("写入成功"); p += 1
            else: F("写入失败"); f += 1
            if entry and len(entry.id) == 12: P("id长度=12"); p += 1
            else: F(f"id={entry.id if entry else 'None'}"); f += 1
        finally: db.close()

        # ===== 16. 边界值 importance=80/40/39 =====
        print("\n【测试16】边界值：80≥✓ 40≥✓ 39<✗")
        boundary = [
            {"content": "a80", "importance": 80, "category": "event"},
            {"content": "a40", "importance": 40, "category": "event"},
            {"content": "a39", "importance": 39, "category": "event"},
        ]
        result = summarizer.process("s_bound", boundary)
        if result["retained"] == 1: P("80 → retained"); p += 1
        else: F(f"retained={result['retained']}"); f += 1
        if result["summarized"] == 1: P("40 → summarized"); p += 1
        else: F(f"summarized={result['summarized']}"); f += 1
        if result["discarded"] == 1: P("39 → discarded"); p += 1
        else: F(f"discarded={result['discarded']}"); f += 1

        # ===== 17. 空列表 =====
        print("\n【测试17】空列表处理")
        r = scorer.score([])
        if r == []: P("Scorer空列表 → []"); p += 1
        else: F(f"len={len(r)}"); f += 1
        r2 = summarizer.process("s_e", [])
        if r2 == {"retained": 0, "summarized": 0, "discarded": 0}: P("Summarizer空列表 → 全0"); p += 1
        else: F(f"={r2}"); f += 1

        # ===== 18. 模块导出 =====
        print("\n【测试18】模块导出")
        from services import MemoryScorer as MS, MemorySummarizer as MS2
        if MS is MemoryScorer: P("MemoryScorer已导出"); p += 1
        else: F("不一致"); f += 1
        if MS2 is MemorySummarizer: P("MemorySummarizer已导出"); p += 1
        else: F("不一致"); f += 1

        # ===== 19. _save_memory 事务安全 =====
        print("\n【测试19】_save_memory 事务安全")
        source = inspect.getsource(summarizer._save_memory)
        if "rollback" in source: P("含rollback"); p += 1
        else: F("缺rollback"); f += 1
        if "except Exception" in source: P("含except Exception"); p += 1
        else: F("缺except"); f += 1

        # ===== 20. 关键词引擎全覆盖 =====
        print("\n【测试20】关键词引擎无LLM依赖")
        source = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                    "services/memory_scorer.py"), "r").read()
        if "openai" not in source.lower() and "AsyncOpenAI" not in source:
            P("MemoryScorer 无 OpenAI 依赖（纯本地引擎）"); p += 1
        else: F("含 OpenAI 依赖"); f += 1
        source2 = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                     "services/memory_summarizer.py"), "r").read()
        if "openai" not in source2.lower() and "AsyncOpenAI" not in source2:
            P("MemorySummarizer 无 OpenAI 依赖（纯本地引擎）"); p += 1
        else: F("含 OpenAI 依赖"); f += 1

        # ===== 21. 端到端：score → process 全流程 =====
        print("\n【测试21】端到端：score → process 全流程（无LLM）")
        overflow = [
            {"content": "我是张三今年25岁", "role": "user", "id": "1"},
            {"content": "今天天气不错", "role": "user", "id": "2"},
            {"content": "ok", "role": "assistant", "id": "3"},
            {"content": "我很难过因为工作不顺利", "role": "user", "id": "4"},
            {"content": "你好", "role": "user", "id": "5"},
        ]
        scored = scorer.score(overflow)
        if len(scored) == 5: P("score: 5条入→5条出"); p += 1
        else: F(f"len={len(scored)}"); f += 1
        # 第4条含情绪词和决定词，importance应该较高
        if scored[3]["importance"] > scored[2]["importance"]:
            P("情绪内容评分 > 简单回复评分"); p += 1
        else: F("评分不合理"); f += 1
        # category
        if scored[0]["category"] in ["fact", "event", "emotional"]:
            P("分类为 event/fact/emotional 之一"); p += 1
        else: F(f"category={scored[0]['category']}"); f += 1
        # 全流程
        result = summarizer.process("s_e2e", scored)
        if isinstance(result, dict): P("process返回dict"); p += 1
        else: F(f"type={type(result)}"); f += 1
        if sum(result.values()) == 5: P("retained+summarized+discarded = 5"); p += 1
        else: F(f"sum={sum(result.values())}"); f += 1

        # ===== 22. MemoryEntry timestamp 已修复 =====
        print("\n【测试22】MemoryEntry timestamp 使用 timezone-aware")
        source_m = inspect.getsource(summarizer._save_memory)
        if "timezone.utc" in source_m or "datetime.UTC" in source_m:
            P("timestamp 使用 timezone-aware datetime"); p += 1
        else: F("可能使用 utcnow()"); f += 1

        # ===== 汇总 =====
        print("\n" + "=" * 65)
        t = p + f
        print(f"测试总数: {t}  通过: {p}  失败: {f}  通过率: {p/t*100:.1f}%")
        print("=" * 65)

    finally:
        Base.metadata.drop_all(bind=engine)
        try: os.remove("tests/data/test_accept_4_2.db")
        except OSError: pass

    if f == 0: print("\n🎉 Task 4.2 验收通过！")
    else: print("\n❌ Task 4.2 验收未通过！")
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(run())
