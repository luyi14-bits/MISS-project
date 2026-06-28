import os
import json
import pytest
from fastapi.testclient import TestClient

os.environ["DB_URL"] = "sqlite:///./tests/data/test_preset.db"


@pytest.fixture(scope="module")
def init_test_db():
    from models import Base
    from database import engine
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    try:
        os.remove("tests/data/test_preset.db")
    except OSError:
        pass


@pytest.fixture
def client(init_test_db):
    from main import app
    return TestClient(app)


class TestPresetList:
    def test_list_empty(self, client):
        resp = client.get("/api/preset/list")
        assert resp.status_code == 200
        data = resp.json()
        assert data["presets"] == []

    def test_list_with_items(self, client):
        profile = {attr: 0 for attr in [
            "rational_emotional", "willpower", "independent_submissive",
            "education_level", "intimacy", "curiosity", "humor",
            "aggression", "social_energy", "adventurousness"
        ]}
        profile["intimacy"] = 0
        profile["allowed_domains"] = []
        client.post("/api/preset/save", json={"name": "Test Preset", "profile": profile})
        client.post("/api/preset/save", json={"name": "Another", "profile": profile})
        resp = client.get("/api/preset/list")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["presets"]) == 2


class TestPresetSave:
    def test_save_default_profile(self, client):
        profile = {attr: 0 for attr in [
            "rational_emotional", "willpower", "independent_submissive",
            "education_level", "intimacy", "curiosity", "humor",
            "aggression", "social_energy", "adventurousness"
        ]}
        profile["intimacy"] = 0
        profile["allowed_domains"] = []
        resp = client.post("/api/preset/save", json={"name": "Default", "profile": profile})
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "预设已保存"
        assert "id" in data
        assert len(data["id"]) == 12

    def test_save_with_cirno_profile(self, client):
        profile = {attr: 0 for attr in [
            "rational_emotional", "willpower", "independent_submissive",
            "education_level", "intimacy", "curiosity", "humor",
            "aggression", "social_energy", "adventurousness"
        ]}
        profile["education_level"] = -100
        profile["allowed_domains"] = ["艺术"]
        profile["intimacy"] = 0
        resp = client.post("/api/preset/save", json={"name": "Cirno Mode", "profile": profile})
        assert resp.status_code == 200


class TestPresetGet:
    def test_get_existing_preset(self, client):
        profile = {attr: 0 for attr in [
            "rational_emotional", "willpower", "independent_submissive",
            "education_level", "intimacy", "curiosity", "humor",
            "aggression", "social_energy", "adventurousness"
        ]}
        profile["intimacy"] = 0
        profile["allowed_domains"] = []
        save_resp = client.post("/api/preset/save", json={"name": "Get Me", "profile": profile})
        pid = save_resp.json()["id"]

        resp = client.get(f"/api/preset/{pid}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Get Me"
        assert data["profile"]["rational_emotional"] == 0

    def test_get_nonexistent_preset(self, client):
        resp = client.get("/api/preset/nonexistent_id")
        assert resp.status_code == 404


class TestPresetDelete:
    def test_delete_existing(self, client):
        profile = {attr: 0 for attr in [
            "rational_emotional", "willpower", "independent_submissive",
            "education_level", "intimacy", "curiosity", "humor",
            "aggression", "social_energy", "adventurousness"
        ]}
        profile["intimacy"] = 0
        profile["allowed_domains"] = []
        save_resp = client.post("/api/preset/save", json={"name": "To Delete", "profile": profile})
        pid = save_resp.json()["id"]

        resp = client.delete(f"/api/preset/{pid}")
        assert resp.status_code == 200
        assert resp.json()["message"] == "预设已删除"

        get_resp = client.get(f"/api/preset/{pid}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent(self, client):
        resp = client.delete("/api/preset/nonexistent_id")
        assert resp.status_code == 404


class TestPresetApply:
    def test_apply_existing_preset(self, client):
        profile = {attr: 0 for attr in [
            "rational_emotional", "willpower", "independent_submissive",
            "education_level", "intimacy", "curiosity", "humor",
            "aggression", "social_energy", "adventurousness"
        ]}
        profile["education_level"] = 50
        profile["intimacy"] = 0
        profile["allowed_domains"] = ["科学"]
        save_resp = client.post("/api/preset/save", json={"name": "Apply Me", "profile": profile})
        pid = save_resp.json()["id"]

        resp = client.post("/api/preset/apply", json={"preset_id": pid})
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "预设已应用"
        assert data["profile"]["education_level"] == 50
        assert data["profile"]["allowed_domains"] == ["科学"]

    def test_apply_nonexistent_preset(self, client):
        resp = client.post("/api/preset/apply", json={"preset_id": "nonexistent_id"})
        assert resp.status_code == 404


class TestPresetExport:
    def test_export_existing(self, client):
        profile = {attr: 0 for attr in [
            "rational_emotional", "willpower", "independent_submissive",
            "education_level", "intimacy", "curiosity", "humor",
            "aggression", "social_energy", "adventurousness"
        ]}
        profile["education_level"] = -100
        profile["intimacy"] = 0
        profile["allowed_domains"] = []
        save_resp = client.post("/api/preset/save", json={"name": "Export Me", "profile": profile})
        pid = save_resp.json()["id"]

        resp = client.get(f"/api/preset/{pid}/export")
        assert resp.status_code == 200
        data = resp.json()
        assert data["version"] == "1.1"
        assert data["name"] == "Export Me"
        assert data["easter_egg_hint"] is not None
        assert "⑨" in data["easter_egg_hint"]

    def test_export_nonexistent(self, client):
        resp = client.get("/api/preset/nonexistent/export")
        assert resp.status_code == 404


class TestPresetImport:
    def test_import_valid_json(self, client):
        export_data = {
            "version": "1.0",
            "name": "Import Test",
            "profile": {
                "rational_emotional": 50,
                "willpower": 30,
                "independent_submissive": -20,
                "education_level": 80,
                "intimacy": 10,
                "curiosity": 60,
                "humor": 40,
                "aggression": -10,
                "social_energy": 20,
                "adventurousness": 90,
                "allowed_domains": ["人文"],
            },
        }
        files = {"file": ("test_preset.json", json.dumps(export_data), "application/json")}
        resp = client.post("/api/preset/import", files=files)
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "预设已导入"
        assert data["profile"]["education_level"] == 80

    def test_import_invalid_file_type(self, client):
        files = {"file": ("test.txt", b"not json", "text/plain")}
        resp = client.post("/api/preset/import", files=files)
        assert resp.status_code == 400
