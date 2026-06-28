import os
import sys
import pytest

os.environ["DB_URL"] = "sqlite:///./tests/data/test_prompt_builder.db"

from models import Base
from database import engine, SessionLocal
from services.prompt_builder import PromptBuilder
from services.attribute_engine import MISSProfile


@pytest.fixture(scope="module")
def init_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    try:
        os.remove("tests/data/test_prompt_builder.db")
    except OSError:
        pass


@pytest.fixture
def builder(init_test_db):
    return PromptBuilder()


class TestPromptBuilder:
    def seed_conversation(self, session_id: str, messages: list[dict]):
        from services.memory_manager import ConversationStore
        store = ConversationStore()
        for msg in messages:
            store.add_message(session_id, msg["role"], msg["content"])

    def test_build_returns_list_of_dicts(self, builder):
        result = builder.build("s1", "你好", MISSProfile())
        assert isinstance(result, list)
        assert len(result) >= 2
        for item in result:
            assert "role" in item
            assert "content" in item

    def test_build_has_system_message_first(self, builder):
        result = builder.build("s1", "你好", MISSProfile())
        assert result[0]["role"] == "system"

    def test_build_has_user_message_last(self, builder):
        result = builder.build("s2", "今天心情怎么样？", MISSProfile())
        assert result[-1]["role"] == "user"
        assert result[-1]["content"] == "今天心情怎么样？"

    def test_build_empty_conversation_has_two_messages(self, builder):
        result = builder.build("s3", "你好", MISSProfile())
        assert len(result) == 2

    def test_build_with_conversation_history(self, builder):
        sid = "s_hist"
        self.seed_conversation(sid, [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好呀！"},
            {"role": "user", "content": "今天天气不错"},
            {"role": "assistant", "content": "是啊，阳光很好"},
        ])
        result = builder.build(sid, "我们出去走走吧", MISSProfile())
        assert len(result) == 4 + 2  # 4 history + system + new user
        assert result[0]["role"] == "system"
        assert result[1]["role"] == "user"
        assert result[1]["content"] == "你好"
        assert result[4]["content"] == "是啊，阳光很好"
        assert result[-1]["content"] == "我们出去走走吧"

    def test_build_window_respects_limit(self, builder):
        sid = "s_limit"
        messages = []
        for i in range(30):
            messages.append({"role": "user", "content": f"消息{i}"})
            messages.append({"role": "assistant", "content": f"回复{i}"})
        self.seed_conversation(sid, messages)
        result = builder.build(sid, "最新消息", MISSProfile())
        history_count = len(result) - 2
        assert history_count <= 20
        assert result[-1]["content"] == "最新消息"

    def test_build_system_prompt_contains_default_name(self, builder):
        result = builder.build("s4", "你好", MISSProfile())
        system = result[0]["content"]
        assert "MISS小姐" in system

    def test_build_system_prompt_cirno_mode(self, builder):
        profile = MISSProfile(education_level=-100)
        result = builder.build("s5", "什么是量子物理？", profile)
        system = result[0]["content"]
        assert "MISS⑨" in system
        assert "BAKA~" in system

    def test_build_with_cross_effects(self, builder):
        profile = MISSProfile(education_level=-100, curiosity=100)
        result = builder.build("s6", "给我讲讲宇宙吧", profile)
        system = result[0]["content"]
        assert "好奇笨蛋" in system

    def test_build_with_allowed_domains(self, builder):
        profile = MISSProfile(allowed_domains=["艺术", "人文", "科学"])
        result = builder.build("s7", "你好", profile)
        system = result[0]["content"]
        assert "艺术、人文、科学" in system

    def test_build_system_prompt_contains_required_sections(self, builder):
        result = builder.build("s8", "你好", MISSProfile())
        system = result[0]["content"]
        required_sections = [
            "system_directive",
            "persona",
            "dynamic_state",
            "knowledge_ceiling",
            "cognitive_engine",
            "behavioral_constraints",
            "response_format",
        ]
        for section in required_sections:
            assert f"<{section}>" in system, f"Missing section: {section}"

    def test_build_system_prompt_contains_all_attributes(self, builder):
        result = builder.build("s9", "你好", MISSProfile())
        system = result[0]["content"]
        attrs = [
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
        for attr in attrs:
            assert f"<{attr}" in system, f"Missing attribute: {attr}"

    def test_build_with_cross_effects_and_cirno(self, builder):
        profile = MISSProfile(
            education_level=-100,
            curiosity=100,
            social_energy=100,
            adventurousness=100,
        )
        result = builder.build("s10", "带我去冒险吧！", profile)
        system = result[0]["content"]
        assert "好奇笨蛋" in system
        assert "派对狂人" in system
        assert "MISS⑨" in system

    def test_build_messages_structure_is_valid_openai_format(self, builder):
        result = builder.build("s11", "测试消息", MISSProfile())
        for msg in result:
            assert msg["role"] in ("system", "user", "assistant")
            assert isinstance(msg["content"], str)
            assert len(msg["content"]) > 0

    def test_build_tsundere_lover_combo(self, builder):
        profile = MISSProfile(independent_submissive=-100, intimacy=100)
        result = builder.build("s12", "我想你了", profile)
        system = result[0]["content"]
        assert "傲娇恋人" in system
