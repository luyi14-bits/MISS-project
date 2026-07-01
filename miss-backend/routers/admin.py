# Copyright (C) 2026  MISS Project Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
from fastapi import APIRouter, Request

from limiter import limiter
from database import SessionLocal
from models.session import Session
from models.message import Message as MessageModel
from models.memory import MemoryEntry
from services.memory_scorer import MemoryScorer
from services.memory_summarizer import MemorySummarizer
from services.vector_store import VectorMemoryStore


router = APIRouter()
_scorer = MemoryScorer()
_vector_store = VectorMemoryStore()


@router.get("/stats")
@limiter.limit("30/minute")
async def admin_stats(request: Request):
    db = SessionLocal()
    try:
        session_count = db.query(Session).count()
        message_count = db.query(MessageModel).count()
        memory_count = db.query(MemoryEntry).count()
        try:
            vector_count = _vector_store.count()
        except Exception:
            vector_count = 0

        avg_importance = 0
        if memory_count > 0:
            total = db.query(MemoryEntry.importance).all()
            avg_importance = round(sum(r[0] for r in total) / memory_count, 1)

        category_counts = {
            "event": db.query(MemoryEntry).filter(MemoryEntry.category == "event").count(),
            "fact": db.query(MemoryEntry).filter(MemoryEntry.category == "fact").count(),
            "emotional": db.query(MemoryEntry).filter(MemoryEntry.category == "emotional").count(),
        }

        return {
            "sessions": session_count,
            "messages": message_count,
            "memories": memory_count,
            "vector_entries": vector_count,
            "avg_importance": avg_importance,
            "categories": category_counts,
        }
    finally:
        db.close()


@router.post("/memory/compact")
@limiter.limit("2/hour")
async def compact_memories(request: Request, session_id: str | None = None):
    db = SessionLocal()
    try:
        if session_id:
            sessions = [session_id]
        else:
            recent = (
                db.query(Session.id)
                .order_by(Session.updated_at.desc())
                .limit(50)
                .all()
            )
            sessions = [r[0] for r in recent]
    finally:
        db.close()

    summarizer = MemorySummarizer(vector_store=_vector_store)
    total = {"retained": 0, "summarized": 0, "discarded": 0}

    for sid in sessions:
        db = SessionLocal()
        try:
            total_msgs = (
                db.query(MessageModel)
                .filter(MessageModel.session_id == sid)
                .count()
            )
        finally:
            db.close()

        if total_msgs <= 20:
            continue
        if total_msgs > 200:
            total_msgs = 200

        db = SessionLocal()
        try:
            overflow = (
                db.query(MessageModel)
                .filter(MessageModel.session_id == sid)
                .order_by(MessageModel.timestamp.asc())
                .limit(total_msgs - 20)
                .all()
            )
            overflow_dicts = [
                {"id": r.id, "role": r.role, "content": r.content, "timestamp": r.timestamp.isoformat() if r.timestamp else None}
                for r in overflow
            ]
        finally:
            db.close()

        if not overflow_dicts:
            continue

        scored = _scorer.score(overflow_dicts)
        result = summarizer.process(sid, scored)
        total["retained"] += result["retained"]
        total["summarized"] += result["summarized"]
        total["discarded"] += result["discarded"]

    return {"message": "记忆压缩完成", "stats": total}


@router.post("/memory/age")
@limiter.limit("2/hour")
async def age_memories(request: Request, max_age_days: int = 30):
    result = _vector_store.age(max_age_days=max_age_days)
    return {"message": "记忆老化处理完成", "stats": result}
