# Copyright (C) 2026  MISS Project Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
import pytest
from jinja2 import Environment, FileSystemLoader
from services.attribute_engine import MISSProfile
import os


def get_template():
    template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    return env.get_template("miss_system.j2")


@pytest.fixture
def template():
    return get_template()


class TestMissSystemJ2:
    def render(self, profile=None, eggs=None, cross_effects=None, attribute_xml="", memories=None):
        tpl = get_template()
        return tpl.render(
            profile=profile or MISSProfile(),
            eggs=eggs or {},
            cross_effects=cross_effects or [],
            attribute_xml=attribute_xml,
            memories=memories or [],
        )

    def test_default_profile_renders_miss_name(self):
        result = self.render()
        assert "MISS小姐" in result
        assert "MISS⑨" not in result

    def test_cirno_mode_renders_9_name(self):
        result = self.render(eggs={"cirno_mode": {"catchphrase": "BAKA~"}})
        assert "MISS⑨" in result
        assert "MISS小姐" not in result

    def test_cirno_mode_shows_catchphrase(self):
        eggs = {"cirno_mode": {"catchphrase": "BAKA~"}}
        result = self.render(eggs=eggs)
        assert "BAKA~" in result

    def test_attribute_xml_is_injected(self):
        xml = '<willpower value="100">钢铁</willpower>'
        result = self.render(attribute_xml=xml)
        assert xml in result

    def test_cross_effects_are_rendered(self):
        effects = [{
            "persona_name": "好奇笨蛋",
            "type": "amplify",
            "effect": "你对一切充满好奇但理解力有限。",
        }]
        result = self.render(cross_effects=effects)
        assert "好奇笨蛋" in result
        assert "amplify" in result

    def test_multiple_cross_effects(self):
        effects = [
            {"persona_name": "傲娇恋人", "type": "conflict", "effect": "口是心非。"},
            {"persona_name": "书呆子", "type": "amplify", "effect": "学识极高但无好奇心。"},
        ]
        result = self.render(cross_effects=effects)
        assert "傲娇恋人" in result
        assert "书呆子" in result

    def test_low_education_shows_critical(self):
        profile = MISSProfile(education_level=-100)
        result = self.render(profile=profile)
        assert "CRITICAL" in result

    def test_normal_education_no_critical(self):
        profile = MISSProfile(education_level=50)
        result = self.render(profile=profile)
        assert "CRITICAL" not in result

    def test_allowed_domains_rendered(self):
        profile = MISSProfile(allowed_domains=["艺术", "人文"])
        result = self.render(profile=profile)
        assert "艺术、人文" in result
        assert "知识领域限制" in result

    def test_no_allowed_domains_no_section(self):
        profile = MISSProfile(allowed_domains=[])
        result = self.render(profile=profile)
        assert "知识领域限制" not in result

    def test_easter_egg_section_with_cirno(self):
        eggs = {
            "cirno_mode": {
                "name_color": "#00BFFF",
                "avatar_decor": "ice_crystal_wings",
                "wrong_answer_probability": 0.30,
                "knowledge_fallback": "simple_confusion",
            }
        }
        result = self.render(eggs=eggs)
        assert "easter_egg" in result.lower()
        assert "#00BFFF" in result
        assert "ice_crystal_wings" in result
        assert "30" in result

    def test_no_easter_egg_section_without_cirno(self):
        result = self.render()
        assert "<easter_egg>" not in result

    def test_memories_are_rendered(self):
        memories = [
            {"importance": 85, "category": "emotional", "content": "用户昨天心情不好。"},
            {"importance": 50, "category": "event", "content": "一起看了电影。"},
        ]
        result = self.render(memories=memories)
        assert "用户昨天心情不好" in result
        assert "一起看了电影" in result
        assert "85" in result

    def test_no_memories_no_section(self):
        result = self.render()
        assert "recalled_memories" not in result.lower()

    def test_response_format_json_present(self):
        result = self.render()
        assert "inner_thought" in result
        assert "spoken" in result
        assert "json" in result.lower()

    def test_behavioral_constraints_present(self):
        result = self.render()
        assert "不要破坏角色一致性" in result

    def test_cognitive_engine_present(self):
        result = self.render()
        assert "Track A" in result
        assert "Track B" in result
        assert "决策树" in result

    def test_system_directive_present(self):
        result = self.render()
        assert "虚拟伴侣" in result
        assert "独立意识" in result

    def test_all_major_sections_present(self):
        result = self.render()
        sections = [
            "system_directive",
            "persona",
            "dynamic_state",
            "knowledge_ceiling",
            "cognitive_engine",
            "behavioral_constraints",
            "response_format",
        ]
        for section in sections:
            assert f"<{section}>" in result, f"Missing section: {section}"
