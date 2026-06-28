import pytest
from services.llm_caller import _is_reasoning_model, _REASONING_MODELS


class TestReasoningModels:
    def test_recognizes_deepseek_v4_pro(self):
        assert _is_reasoning_model("deepseek-v4-pro")

    def test_recognizes_deepseek_v4_flash(self):
        assert _is_reasoning_model("deepseek-v4-flash")

    def test_reasoning_models_contains_v4(self):
        assert "v4-pro" in _REASONING_MODELS
        assert "v4-flash" in _REASONING_MODELS

    def test_recognizes_o1(self):
        assert _is_reasoning_model("o1-preview")

    def test_recognizes_o3(self):
        assert _is_reasoning_model("o3-mini")

    def test_non_reasoning_models_unchanged(self):
        assert not _is_reasoning_model("gpt-4o")
        assert not _is_reasoning_model("gpt-4o-mini")
