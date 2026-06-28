import pytest
from services.llm_caller import LLMCaller

_parse = LLMCaller._parse_json_response


class TestParseJsonResponse:
    """Tests for _parse_json_response — strict JSON-only parser per security spec."""

    def test_valid_json_parses_correctly(self):
        result = _parse('{"inner_thought": "思考中", "spoken": "你好呀"}')
        assert result["inner_thought"] == "思考中"
        assert result["spoken"] == "你好呀"

    def test_empty_string_returns_empty(self):
        result = _parse("")
        assert result["inner_thought"] == ""
        assert result["spoken"] == ""

    def test_none_returns_empty(self):
        result = _parse("   ")
        assert result["inner_thought"] == ""
        assert result["spoken"] == ""

    def test_plain_text_returns_safe_placeholder(self):
        result = _parse("今天的天气真不错啊，阳光明媚。")
        assert result["inner_thought"] == ""
        assert result["spoken"] == "响应格式异常，请重试"

    def test_markdown_wrapped_json_returns_safe_placeholder(self):
        result = _parse('```json\n{"inner_thought":"思考中","spoken":"你好呀"}\n```')
        assert result["spoken"] == "响应格式异常，请重试"

    def test_truncated_json_returns_safe_placeholder(self):
        result = _parse('{"inner_thought":"思考","spoken":"还没说完')
        assert result["spoken"] == "响应格式异常，请重试"

    def test_json_with_extra_text_returns_safe_placeholder(self):
        result = _parse('some prefix {"inner_thought": "test", "spoken": "hello"} trailing')
        assert result["spoken"] == "响应格式异常，请重试"

    def test_unbalanced_braces_returns_safe_placeholder(self):
        result = _parse('{"inner_thought": "test", "spoken": "hello"} extra }')
        assert result["spoken"] == "响应格式异常，请重试"

    def test_code_block_plain_text_returns_safe_placeholder(self):
        result = _parse('```json\n今天的天气\n```')
        assert result["spoken"] == "响应格式异常，请重试"

    def test_non_object_json_returns_safe_placeholder(self):
        result = _parse('[1, 2, 3]')
        assert result["spoken"] == "响应格式异常，请重试"

    def test_injection_script_returns_safe_placeholder(self):
        result = _parse('<script>alert("xss")</script>')
        assert result["spoken"] == "响应格式异常，请重试"

    def test_extra_fields_preserved(self):
        result = _parse('{"inner_thought": "a", "spoken": "b", "extra": "c"}')
        assert result["inner_thought"] == "a"
        assert result["spoken"] == "b"
