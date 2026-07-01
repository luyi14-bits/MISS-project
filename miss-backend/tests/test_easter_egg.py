# Copyright (C) 2026  MISS Project Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
import pytest
from services.attribute_engine import MISSProfile, EasterEggEngine


class TestEasterEggEngine:
    def setup_method(self):
        self.engine = EasterEggEngine()

    def test_cirno_mode_triggers_at_minus_100(self):
        profile = MISSProfile(education_level=-100)
        eggs = self.engine.evaluate(profile)
        assert "cirno_mode" in eggs
        assert eggs["cirno_mode"]["name_suffix"] == "⑨"
        assert eggs["cirno_mode"]["catchphrase"] == "BAKA~"
        assert eggs["cirno_mode"]["catchphrase_frequency"] == 0.25
        assert eggs["cirno_mode"]["name_color"] == "#00BFFF"
        assert eggs["cirno_mode"]["avatar_decor"] == "ice_crystal_wings"
        assert eggs["cirno_mode"]["knowledge_fallback"] == "simple_confusion"
        assert eggs["cirno_mode"]["wrong_answer_probability"] == 0.30

    def test_cirno_mode_not_trigger_at_minus_99(self):
        profile = MISSProfile(education_level=-99)
        eggs = self.engine.evaluate(profile)
        assert eggs == {}

    def test_cirno_mode_not_trigger_at_zero(self):
        profile = MISSProfile(education_level=0)
        eggs = self.engine.evaluate(profile)
        assert eggs == {}

    def test_cirno_mode_not_trigger_at_100(self):
        profile = MISSProfile(education_level=100)
        eggs = self.engine.evaluate(profile)
        assert eggs == {}

    def test_other_attributes_do_not_affect_cirno(self):
        profile = MISSProfile(
            education_level=-100,
            rational_emotional=100,
            curiosity=-100,
            intimacy=100,
        )
        eggs = self.engine.evaluate(profile)
        assert "cirno_mode" in eggs
        assert len(eggs) == 1

    def test_empty_profile_returns_empty(self):
        profile = MISSProfile()
        eggs = self.engine.evaluate(profile)
        assert eggs == {}
