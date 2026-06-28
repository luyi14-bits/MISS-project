import os
import pytest

os.environ["DB_URL"] = "sqlite:///./tests/data/test_memory_scorer.db"


@pytest.fixture(scope="module")
def init_test_db():
    from models import Base
    from database import engine
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    try:
        os.remove("tests/data/test_memory_scorer.db")
    except OSError:
        pass


class TestMemoryScorer:
    def test_constructor_no_args(self):
        from services.memory_scorer import MemoryScorer
        scorer = MemoryScorer()
        assert scorer is not None

    def test_score_empty_returns_empty(self):
        from services.memory_scorer import MemoryScorer
        scorer = MemoryScorer()
        result = scorer.score([])
        assert result == []

    def test_score_single_message_has_all_fields(self):
        from services.memory_scorer import MemoryScorer
        scorer = MemoryScorer()
        msgs = [{"content": "你好", "role": "user", "id": "m1"}]
        result = scorer.score(msgs)
        assert len(result) == 1
        assert result[0]["content"] == "你好"
        assert result[0]["role"] == "user"
        assert result[0]["id"] == "m1"
        assert "importance" in result[0]
        assert "category" in result[0]

    def test_score_importance_in_range(self):
        from services.memory_scorer import MemoryScorer
        scorer = MemoryScorer()
        msgs = [
            {"content": "短", "role": "assistant", "id": "a"},
            {"content": "我叫小明，今年25岁，我喜欢打篮球，我决定明天去旅行", "role": "user", "id": "b"},
        ]
        result = scorer.score(msgs)
        for item in result:
            assert 0 <= item["importance"] <= 100

    def test_score_category_is_valid(self):
        from services.memory_scorer import MemoryScorer
        scorer = MemoryScorer()
        msgs = [
            {"content": "今天天气真好", "role": "user", "id": "a"},
            {"content": "我很开心！太好了～", "role": "user", "id": "b"},
        ]
        result = scorer.score(msgs)
        for item in result:
            assert item["category"] in ("event", "fact", "emotional")

    def test_role_user_gets_higher_score_than_assistant(self):
        from services.memory_scorer import MemoryScorer
        scorer = MemoryScorer()
        msgs = [
            {"content": "hi", "role": "assistant", "id": "a"},
            {"content": "hi", "role": "user", "id": "b"},
        ]
        result = scorer.score(msgs)
        assert result[1]["importance"] > result[0]["importance"]

    def test_longer_content_gets_higher_score(self):
        from services.memory_scorer import MemoryScorer
        scorer = MemoryScorer()
        msgs = [
            {"content": "短", "role": "assistant", "id": "a"},
            {"content": "这是一条非常长的用户消息，包含了很多详细的信息和描述，应该获得更高的长度分数", "role": "assistant", "id": "b"},
        ]
        result = scorer.score(msgs)
        assert result[1]["importance"] > result[0]["importance"]

    def test_keywords_increase_score(self):
        from services.memory_scorer import MemoryScorer
        scorer = MemoryScorer()
        msgs = [
            {"content": "hello", "role": "user", "id": "a"},
            {"content": "我叫张三 我喜欢音乐 我决定学习钢琴", "role": "user", "id": "b"},
        ]
        result = scorer.score(msgs)
        assert result[1]["importance"] > result[0]["importance"]

    def test_emotional_punctuation_increases_score(self):
        from services.memory_scorer import MemoryScorer
        scorer = MemoryScorer()
        msgs = [
            {"content": "hello", "role": "user", "id": "a"},
            {"content": "真的吗！？不会吧～～～！！", "role": "user", "id": "b"},
        ]
        result = scorer.score(msgs)
        assert result[1]["importance"] > result[0]["importance"]

    def test_score_preserves_message_count(self):
        from services.memory_scorer import MemoryScorer
        scorer = MemoryScorer()
        msgs = [
            {"content": f"msg{i}", "role": "user", "id": str(i)}
            for i in range(10)
        ]
        result = scorer.score(msgs)
        assert len(result) == 10

    def test_classify_emotional(self):
        from services.memory_scorer import MemoryScorer
        scorer = MemoryScorer()
        assert scorer._classify("我今天很开心很感动") == "emotional"

    def test_classify_event(self):
        from services.memory_scorer import MemoryScorer
        scorer = MemoryScorer()
        assert scorer._classify("我去了商店买了一件衣服") == "event"

    def test_classify_fact(self):
        from services.memory_scorer import MemoryScorer
        scorer = MemoryScorer()
        assert scorer._classify("地球是圆的") == "fact"

    def test_classify_emotional_vs_event(self):
        from services.memory_scorer import MemoryScorer
        scorer = MemoryScorer()
        assert scorer._classify("开心 难过 感动 我去商店") == "emotional"

    def test_classify_event_over_empty(self):
        from services.memory_scorer import MemoryScorer
        scorer = MemoryScorer()
        assert scorer._classify("我去了北京") == "event"


class TestMemorySummarizer:
    def test_process_empty(self, init_test_db):
        from services.memory_summarizer import MemorySummarizer
        summarizer = MemorySummarizer()
        result = summarizer.process("s1", [])
        assert result == {"retained": 0, "summarized": 0, "discarded": 0}

    def test_process_high_importance_retains(self, init_test_db):
        from services.memory_summarizer import MemorySummarizer
        from database import SessionLocal
        from models.memory import MemoryEntry
        summarizer = MemorySummarizer()
        scored = [
            {"content": "Important info about user preferences", "importance": 90, "category": "fact"},
        ]
        result = summarizer.process("s_test", scored)
        assert result["retained"] == 1
        assert result["discarded"] == 0
        assert result["summarized"] == 0

        db = SessionLocal()
        try:
            entry = db.query(MemoryEntry).filter(MemoryEntry.session_id == "s_test").first()
            assert entry is not None
            assert entry.importance == 90
            assert entry.content == "Important info about user preferences"
        finally:
            db.close()

    def test_process_low_importance_discards(self, init_test_db):
        from services.memory_summarizer import MemorySummarizer
        from database import SessionLocal
        from models.memory import MemoryEntry
        summarizer = MemorySummarizer()
        scored = [
            {"content": "hello world casual greeting", "importance": 10, "category": "event"},
        ]
        result = summarizer.process("s_discard", scored)
        assert result["discarded"] == 1
        assert result["retained"] == 0

        db = SessionLocal()
        try:
            count = db.query(MemoryEntry).filter(MemoryEntry.session_id == "s_discard").count()
            assert count == 0
        finally:
            db.close()

    def test_process_mid_generates_summary(self, init_test_db):
        from services.memory_summarizer import MemorySummarizer
        from database import SessionLocal
        from models.memory import MemoryEntry
        summarizer = MemorySummarizer()
        scored = [
            {"content": "用户说他今天去了一家很不错的咖啡馆，那里的手冲咖啡很棒", "importance": 60, "category": "event"},
        ]
        result = summarizer.process("s_mid", scored)
        assert result["summarized"] == 1

        db = SessionLocal()
        try:
            entry = db.query(MemoryEntry).filter(MemoryEntry.session_id == "s_mid").first()
            assert entry is not None
            assert entry.importance == 60
        finally:
            db.close()

    def test_process_mixed_tiers(self, init_test_db):
        from services.memory_summarizer import MemorySummarizer
        from database import SessionLocal
        from models.memory import MemoryEntry
        summarizer = MemorySummarizer()
        scored = [
            {"content": "Critical user info: allergic to peanuts", "importance": 95, "category": "fact"},
            {"content": "Regular chat about weather", "importance": 50, "category": "event"},
            {"content": "hi", "importance": 5, "category": "event"},
        ]
        result = summarizer.process("s_mix", scored)
        assert result["retained"] == 1
        assert result["summarized"] == 1
        assert result["discarded"] == 1

        db = SessionLocal()
        try:
            count = db.query(MemoryEntry).filter(MemoryEntry.session_id == "s_mix").count()
            assert count == 2
        finally:
            db.close()

    def test_extract_summary_short(self):
        from services.memory_summarizer import MemorySummarizer
        summarizer = MemorySummarizer()
        assert summarizer._extract_summary("Hi") == "Hi"
        assert summarizer._extract_summary("x" * 40) == "x" * 40

    def test_extract_summary_long(self):
        from services.memory_summarizer import MemorySummarizer
        summarizer = MemorySummarizer()
        result = summarizer._extract_summary(
            "用户正在详细描述自己的行程安排和计划内容。接下来他还要继续说明很多事情。"
        )
        assert len(result) <= 50
        assert result.endswith("。")

    def test_extract_summary_no_sep(self):
        from services.memory_summarizer import MemorySummarizer
        summarizer = MemorySummarizer()
        long = "这是一条非常长的消息没有标点符号只能用截断方式处理而且还要继续写更多的内容来超过五十个字符的限制才能触发截断逻辑"
        result = summarizer._extract_summary(long)
        assert result.endswith("...")
        assert len(result) <= 53

    def test_save_memory_writes_to_db(self, init_test_db):
        from services.memory_summarizer import MemorySummarizer
        from database import SessionLocal
        from models.memory import MemoryEntry
        summarizer = MemorySummarizer()
        summarizer._save_memory("s_write", "test content", 75, "fact")

        db = SessionLocal()
        try:
            entry = db.query(MemoryEntry).filter(MemoryEntry.session_id == "s_write").first()
            assert entry is not None
            assert entry.content == "test content"
            assert entry.importance == 75
            assert entry.category == "fact"
            assert len(entry.id) == 12
        finally:
            db.close()


class TestModuleExports:
    def test_memory_scorer_exported(self):
        from services import MemoryScorer, MemorySummarizer
        assert MemoryScorer is not None
        assert MemorySummarizer is not None

    def test_memory_scorer_importable_directly(self):
        from services.memory_scorer import MemoryScorer
        from services.memory_summarizer import MemorySummarizer
        assert MemoryScorer is not None
        assert MemorySummarizer is not None
