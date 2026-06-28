import os
import pytest

os.environ["DB_URL"] = "sqlite:///./tests/data/test_chat_api.db"
os.environ["OPENAI_API_KEY"] = ""

from fastapi.testclient import TestClient
from models import Base
from database import engine


@pytest.fixture(scope="module")
def init_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    try:
        os.remove("tests/data/test_chat_api.db")
    except OSError:
        pass


@pytest.fixture
def client(init_test_db):
    from main import app
    return TestClient(app)


class TestChatAPI:
    def test_chat_returns_200(self, client):
        payload = {
            "session_id": "s1",
            "message": "你好",
            "profile": {},
        }
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 200

    def test_chat_response_has_required_fields(self, client):
        response = client.post("/api/chat", json={
            "session_id": "s2",
            "message": "今天心情怎么样？",
        })
        data = response.json()
        assert "inner_thought" in data
        assert "spoken" in data
        assert "active_easter_eggs" in data
        assert "active_cross_effects" in data

    def test_chat_active_easter_eggs_is_list(self, client):
        response = client.post("/api/chat", json={
            "session_id": "s3",
            "message": "你好",
        })
        data = response.json()
        assert isinstance(data["active_easter_eggs"], list)

    def test_chat_active_cross_effects_is_list(self, client):
        response = client.post("/api/chat", json={
            "session_id": "s4",
            "message": "你好",
        })
        data = response.json()
        assert isinstance(data["active_cross_effects"], list)

    def test_chat_cirno_triggers_easter_egg(self, client):
        payload = {
            "session_id": "s5",
            "message": "什么是量子物理？",
            "profile": {"education_level": -100},
        }
        response = client.post("/api/chat", json=payload)
        data = response.json()
        assert "cirno_mode" in data["active_easter_eggs"]

    def test_chat_cross_effects_triggered(self, client):
        payload = {
            "session_id": "s6",
            "message": "你好",
            "profile": {"education_level": -100, "curiosity": 100},
        }
        response = client.post("/api/chat", json=payload)
        data = response.json()
        effect_ids = [e["id"] for e in data["active_cross_effects"]]
        assert "curious_baka" in effect_ids

    def test_chat_default_profile(self, client):
        response = client.post("/api/chat", json={
            "session_id": "s7",
            "message": "你好",
        })
        data = response.json()
        assert data["active_easter_eggs"] == []

    def test_chat_accepts_full_profile(self, client):
        payload = {
            "session_id": "s8",
            "message": "你好",
            "profile": {
                "rational_emotional": 50,
                "willpower": 30,
                "independent_submissive": -20,
                "education_level": 80,
                "intimacy": 60,
                "curiosity": 70,
                "humor": 90,
                "aggression": -50,
                "social_energy": 20,
                "adventurousness": 40,
                "allowed_domains": ["艺术", "科学"],
            },
        }
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 200

    def test_chat_invalid_profile_returns_422(self, client):
        payload = {
            "session_id": "s9",
            "message": "你好",
            "profile": {"education_level": 999},
        }
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 422

    def test_chat_invalid_intimacy_negative_returns_422(self, client):
        payload = {
            "session_id": "s10",
            "message": "你好",
            "profile": {"intimacy": -1},
        }
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 422

    def test_chat_missing_session_id_returns_422(self, client):
        response = client.post("/api/chat", json={"message": "你好"})
        assert response.status_code == 422

    def test_chat_missing_message_returns_422(self, client):
        response = client.post("/api/chat", json={"session_id": "s12"})
        assert response.status_code == 422

    def test_chat_tsundere_combo(self, client):
        payload = {
            "session_id": "s13",
            "message": "我想你了",
            "profile": {"independent_submissive": -100, "intimacy": 100},
        }
        response = client.post("/api/chat", json=payload)
        data = response.json()
        effect_ids = [e["id"] for e in data["active_cross_effects"]]
        assert "tsundere_lover" in effect_ids

    def test_chat_cross_effect_has_correct_structure(self, client):
        payload = {
            "session_id": "s14",
            "message": "你好",
            "profile": {"education_level": -100, "curiosity": 100},
        }
        response = client.post("/api/chat", json=payload)
        data = response.json()
        for effect in data["active_cross_effects"]:
            assert "id" in effect
            assert "persona_name" in effect
            assert "type" in effect

    def test_chat_fallback_on_no_api_key(self, client):
        response = client.post("/api/chat", json={
            "session_id": "s15",
            "message": "你好",
        })
        data = response.json()
        assert data["spoken"]
