# Copyright (C) 2026  MISS Project Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
import json
import re
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from limiter import limiter
from services.attribute_engine import MISSProfile
from services.llm_caller import LLMCaller
from config import get_model

router = APIRouter()

ATTR_META = [
    ("rational_emotional", "理性/情绪", -100, 100),
    ("willpower", "意志力", -100, 100),
    ("independent_submissive", "独立/顺从", -100, 100),
    ("education_level", "文化水平", -100, 100),
    ("intimacy", "亲密度", 0, 100),
    ("curiosity", "好奇心", -100, 100),
    ("humor", "幽默感", -100, 100),
    ("aggression", "攻击性", -100, 100),
    ("social_energy", "社交能量", -100, 100),
    ("adventurousness", "冒险精神", -100, 100),
]

_caller = LLMCaller()


class CharacterAnalyzeRequest(BaseModel):
    description: str


@router.post("/character/analyze")
@limiter.limit("5/minute")
async def analyze_character(request: Request, req: CharacterAnalyzeRequest):
    _caller.flush_client()

    result = await _caller.analyze_character(req.description)

    if result.get("_error"):
        raise HTTPException(status_code=502, detail=result.get("message", "角色分析失败"))

    MISSProfile.model_validate(result)
    return {"profile": result}
