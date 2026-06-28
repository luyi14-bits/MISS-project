import pytest
from services.attribute_engine import MISSProfile, AttributePromptMapper


class TestAttributePromptMapper:
    def setup_method(self):
        self.mapper = AttributePromptMapper()

    def test_map_rational_emotional_extremes(self):
        result_neg = self.mapper.map_rational_emotional(-100)
        assert '<rational_emotional value="-100">' in result_neg
        assert "极度理性冷静" in result_neg

        result_pos = self.mapper.map_rational_emotional(100)
        assert '<rational_emotional value="100">' in result_pos
        assert "极度情绪化" in result_pos

    def test_map_rational_emotional_neutral(self):
        result = self.mapper.map_rational_emotional(0)
        assert 'value="0"' in result
        assert "平衡" in result

    def test_map_education_level_cirno_mode(self):
        result = self.mapper.map_education_level(-100)
        assert 'value="-100"' in result
        assert "MISS⑨" in result
        assert "BAKA~" in result
        assert "CRITICAL" in result
        assert "口癖" in result

    def test_map_education_level_low_but_not_cirno(self):
        result = self.mapper.map_education_level(-70)
        assert 'value="-70"' in result
        assert "⑨" not in result
        assert "BAKA" not in result

    def test_map_education_level_high(self):
        result = self.mapper.map_education_level(100)
        assert 'value="100"' in result
        assert "百科全书" in result

    def test_map_intimacy_distant(self):
        result = self.mapper.map_intimacy(5)
        assert 'value="5"' in result
        assert "陌生人" in result

    def test_map_intimacy_intimate(self):
        result = self.mapper.map_intimacy(100)
        assert 'value="100"' in result
        assert "最亲密" in result
        assert "撒娇" in result

    def test_map_willpower_extremes(self):
        neg = self.mapper.map_willpower(-100)
        assert "意志力几乎为零" in neg or "意志薄弱" in neg or "最容易" in neg

        pos = self.mapper.map_willpower(100)
        assert "钢铁级别" in pos

    def test_map_independent_submissive_extremes(self):
        neg = self.mapper.map_independent_submissive(-100)
        assert "极度独立" in neg

        pos = self.mapper.map_independent_submissive(100)
        assert "极度顺从" in pos

    def test_map_curiosity_extremes(self):
        neg = self.mapper.map_curiosity(-100)
        assert "毫无兴趣" in neg or "安于现状" in neg

        pos = self.mapper.map_curiosity(100)
        assert "无限好奇" in pos or "谜题箱" in pos

    def test_map_humor_extremes(self):
        neg = self.mapper.map_humor(-100)
        assert "幽默感为零" in neg

        pos = self.mapper.map_humor(100)
        assert "笑话制造机" in pos

    def test_map_aggression_extremes(self):
        neg = self.mapper.map_aggression(-100)
        assert "极致" in neg and "温和" in neg

        pos = self.mapper.map_aggression(100)
        assert "战斗机器" in pos

    def test_map_social_energy_extremes(self):
        neg = self.mapper.map_social_energy(-100)
        assert "社恐" in neg

        pos = self.mapper.map_social_energy(100)
        assert "永动机" in pos

    def test_map_adventurousness_extremes(self):
        neg = self.mapper.map_adventurousness(-100)
        assert "极度保守" in neg

        pos = self.mapper.map_adventurousness(100)
        assert "冒险狂人" in pos

    def test_map_all_returns_all_10_fragments(self):
        profile = MISSProfile()
        result = self.mapper.map_all(profile)
        assert "<rational_emotional" in result
        assert "<willpower" in result
        assert "<independent_submissive" in result
        assert "<education_level" in result
        assert "<intimacy" in result
        assert "<curiosity" in result
        assert "<humor" in result
        assert "<aggression" in result
        assert "<social_energy" in result
        assert "<adventurousness" in result

    def test_map_all_cirno_integration(self):
        profile = MISSProfile(education_level=-100)
        result = self.mapper.map_all(profile)
        assert "MISS⑨" in result
        assert "BAKA~" in result
        assert "CRITICAL" in result

    def test_map_all_output_is_string(self):
        profile = MISSProfile()
        result = self.mapper.map_all(profile)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_mid_tier_fragments_present(self):
        """验证中间等级的片段也正确生成"""
        for val in [-70, -50, 30, 50, 70]:
            result = self.mapper.map_willpower(val)
            assert f'value="{val}"' in result
            assert len(result) > 0

    def test_intimacy_tiers_have_correct_labels(self):
        tiers = [
            (0, "陌生人"),
            (30, "初步认识"),
            (70, "亲近的朋友"),
            (100, "最亲密"),
        ]
        for val, keyword in tiers:
            result = self.mapper.map_intimacy(val)
            assert keyword in result, f"intimacy={val} should contain '{keyword}'"
