import pytest
from services.attribute_engine import MISSProfile, CrossEffectCalculator


class TestCrossEffectCalculator:
    def setup_method(self):
        self.calc = CrossEffectCalculator()

    def test_curious_baka(self):
        profile = MISSProfile(education_level=-100, curiosity=100)
        effects = self.calc.calculate(profile)
        assert len(effects) >= 1
        curious = next(e for e in effects if e["id"] == "curious_baka")
        assert curious["persona_name"] == "好奇笨蛋"
        assert curious["type"] == "amplify"

    def test_tsundere_lover(self):
        profile = MISSProfile(independent_submissive=-100, intimacy=100)
        effects = self.calc.calculate(profile)
        assert len(effects) >= 1
        tsundere = next(e for e in effects if e["id"] == "tsundere_lover")
        assert tsundere["persona_name"] == "傲娇恋人"
        assert tsundere["type"] == "conflict"

    def test_dramatic_comedian(self):
        profile = MISSProfile(rational_emotional=100, humor=100)
        effects = self.calc.calculate(profile)
        assert len(effects) >= 1
        comedian = next(e for e in effects if e["id"] == "dramatic_comedian")
        assert comedian["persona_name"] == "感性喜剧人"

    def test_volatile_heiress(self):
        profile = MISSProfile(aggression=100, willpower=-100)
        effects = self.calc.calculate(profile)
        assert len(effects) >= 1
        heiress = next(e for e in effects if e["id"] == "volatile_heiress")
        assert heiress["persona_name"] == "暴走千金"
        assert heiress["type"] == "conflict"

    def test_lone_adventurer(self):
        profile = MISSProfile(social_energy=-100, adventurousness=100)
        effects = self.calc.calculate(profile)
        assert len(effects) >= 1
        adventurer = next(e for e in effects if e["id"] == "lone_adventurer")
        assert adventurer["persona_name"] == "孤胆冒险家"

    def test_scholarly_bore(self):
        profile = MISSProfile(education_level=100, curiosity=-100)
        effects = self.calc.calculate(profile)
        assert len(effects) >= 1
        bore = next(e for e in effects if e["id"] == "scholarly_bore")
        assert bore["persona_name"] == "书呆子"

    def test_clingy_koala(self):
        profile = MISSProfile(intimacy=100, independent_submissive=100)
        effects = self.calc.calculate(profile)
        assert len(effects) >= 1
        koala = next(e for e in effects if e["id"] == "clingy_koala")
        assert koala["persona_name"] == "黏人精"

    def test_ice_queen(self):
        profile = MISSProfile(rational_emotional=-100, aggression=-100)
        effects = self.calc.calculate(profile)
        assert len(effects) >= 1
        queen = next(e for e in effects if e["id"] == "ice_queen")
        assert queen["persona_name"] == "冰山美人"

    def test_party_animal(self):
        profile = MISSProfile(social_energy=100, adventurousness=100)
        effects = self.calc.calculate(profile)
        assert len(effects) >= 1
        party = next(e for e in effects if e["id"] == "party_animal")
        assert party["persona_name"] == "派对狂人"

    def test_relentless_warrior(self):
        profile = MISSProfile(willpower=100, aggression=100)
        effects = self.calc.calculate(profile)
        assert len(effects) >= 1
        warrior = next(e for e in effects if e["id"] == "relentless_warrior")
        assert warrior["persona_name"] == "钢铁战士"

    def test_empty_profile_returns_empty(self):
        profile = MISSProfile()
        effects = self.calc.calculate(profile)
        assert effects == []

    def test_near_threshold_not_trigger(self):
        profile = MISSProfile(education_level=-99, curiosity=99)
        effects = self.calc.calculate(profile)
        curious_ids = [e["id"] for e in effects]
        assert "curious_baka" not in curious_ids

    def test_multiple_effects_with_overlap(self):
        profile = MISSProfile(
            education_level=-100,
            curiosity=100,
            social_energy=100,
            adventurousness=100,
        )
        effects = self.calc.calculate(profile)
        effect_ids = {e["id"] for e in effects}
        assert "curious_baka" in effect_ids
        assert "party_animal" in effect_ids
        assert len(effects) == 2

    def test_effects_have_required_fields(self):
        profile = MISSProfile(education_level=-100, curiosity=100)
        effects = self.calc.calculate(profile)
        for e in effects:
            assert "id" in e
            assert "type" in e
            assert "persona_name" in e
            assert "effect" in e
            assert isinstance(e["effect"], str)
            assert len(e["effect"]) > 0
