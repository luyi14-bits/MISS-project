import os
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.exc import OperationalError
from .attribute_engine import (
    MISSProfile,
    EasterEggEngine,
    CrossEffectCalculator,
    AttributePromptMapper,
)
from .memory_manager import ConversationStore
from config import config


class PromptBuilder:
    def __init__(self, vector_store=None):
        template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
        self._jinja_env = Environment(loader=FileSystemLoader(template_dir))
        self._easter_egg_engine = EasterEggEngine()
        self._cross_effect_calc = CrossEffectCalculator()
        self._attribute_mapper = AttributePromptMapper()
        self._conversation_store = ConversationStore()
        self._vector_store = vector_store

    def build(self, session_id: str, user_message: str, profile: MISSProfile, character_background: str = "") -> list[dict]:
        result = self.build_full(session_id, user_message, profile, character_background)
        return result["messages"]

    def build_full(self, session_id: str, user_message: str, profile: MISSProfile, character_background: str = "") -> dict:
        eggs = self._easter_egg_engine.evaluate(profile)
        cross_effects = self._cross_effect_calc.calculate(profile)
        attribute_xml = self._attribute_mapper.map_all(profile)

        recalled = []
        if self._vector_store:
            try:
                recalled = self._vector_store.recall(query=user_message, top_k=5)
            except Exception as e:
                import logging; logging.warning("[降级] vector_store.recall 失败: %s", e)
        if not recalled:
            recalled = self._conversation_store.recall(session_id, user_message)

        system_prompt = self._render_template(profile, eggs, cross_effects, attribute_xml, recalled)

        if character_background and character_background.strip():
            system_prompt = f"【你的人物背景设定】\n{character_background.strip()}\n\n{system_prompt}"

        try:
            conversation_window = self._conversation_store.get_window(
                session_id, n=config.conversation_window_size
            )
        except OperationalError:
            conversation_window = []

        messages = [
            {"role": "system", "content": system_prompt},
            *conversation_window,
            {"role": "user", "content": user_message},
        ]

        active_easter_eggs = [k for k in eggs]
        active_cross_effects = [
            {"id": e["id"], "persona_name": e["persona_name"], "type": e["type"]}
            for e in cross_effects
        ]

        return {
            "messages": messages,
            "active_easter_eggs": active_easter_eggs,
            "active_cross_effects": active_cross_effects,
        }

    def _render_template(
        self,
        profile: MISSProfile,
        eggs: dict,
        cross_effects: list[dict],
        attribute_xml: str,
        memories: list[dict],
    ) -> str:
        template = self._jinja_env.get_template("miss_system.j2")
        return template.render(
            profile=profile,
            eggs=eggs,
            cross_effects=cross_effects,
            attribute_xml=attribute_xml,
            memories=memories,
        )
