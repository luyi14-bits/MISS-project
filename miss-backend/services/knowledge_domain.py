# Copyright (C) 2026  MISS Project Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
import logging


def build_domain_prompt(tags: list[str]) -> str:
    if not tags:
        return ""
    return (
        f"<knowledge_domains>\n"
        f"你只了解以下领域的知识：{'、'.join(tags)}。\n"
        f"如果用户的问题超出你的知识范围，用角色性格自然回应即可。\n"
        f"</knowledge_domains>"
    )
