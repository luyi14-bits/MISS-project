# Copyright (C) 2026  MISS Project Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
PERSONAL_KEYWORDS = [
    "我叫", "我是", "我喜欢", "我讨厌", "我决定",
    "我的", "年龄", "生日", "家在", "工作", "电话", "地址",
]
DECISION_KEYWORDS = ["决定", "打算", "想要", "一定要", "必须", "选择"]
EMOTIONAL_KEYWORDS_KW = [
    "开心", "难过", "生气", "害怕", "担心", "爱",
    "恨", "感动", "失望", "兴奋", "焦虑", "幸福",
]
EMOTIONAL_WORDS_CLASSIFY = [
    "开心", "难过", "生气", "害怕", "担心", "爱", "恨", "感动",
    "失望", "兴奋", "焦虑", "幸福", "喜欢", "讨厌", "想", "烦",
]
EVENT_VERBS = [
    "去", "做", "发生", "买了", "到了", "去了", "吃了", "看了",
    "决定了", "完成", "开始",
]


class MemoryScorer:
    def score(self, overflow_messages: list[dict]) -> list[dict]:
        results = []
        for msg in overflow_messages:
            content = msg.get("content", "")
            role = msg.get("role", "user")

            length_score = min(len(content) / 10, 30)

            kw_score = 0
            for kw in PERSONAL_KEYWORDS + DECISION_KEYWORDS:
                if kw in content:
                    kw_score += 10
            for kw in EMOTIONAL_KEYWORDS_KW:
                if kw in content:
                    kw_score += 5
            kw_score = min(kw_score, 40)

            role_score = 15 if role == "user" else 5

            emotional_density = (
                content.count("！") + content.count("!") +
                content.count("？") + content.count("?") + content.count("～")
            )
            density_score = min(emotional_density * 3, 15)

            importance = min(int(length_score + kw_score + role_score + density_score), 100)

            category = self._classify(content)

            results.append({
                "content": content,
                "importance": importance,
                "category": category,
                "role": role,
                "id": msg.get("id"),
            })
        return results

    def _classify(self, content: str) -> str:
        emotional_count = sum(1 for w in EMOTIONAL_WORDS_CLASSIFY if w in content)
        event_count = sum(1 for v in EVENT_VERBS if v in content)
        if emotional_count > event_count:
            return "emotional"
        elif event_count > 0:
            return "event"
        else:
            return "fact"
