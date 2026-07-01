# Copyright (C) 2026  MISS Project Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
import uuid
from datetime import datetime, timezone
from database import SessionLocal
from models.memory import MemoryEntry
from .crypto import encrypt
import logging


class MemorySummarizer:
    def __init__(self, vector_store=None):
        self._vector_store = vector_store

    def process(self, session_id: str, scored_results: list[dict]) -> dict:
        retained = 0
        summarized = 0
        discarded = 0

        for item in scored_results:
            importance = item.get("importance", 50)
            content = item.get("content", "")
            category = item.get("category", "event")

            if importance >= 80:
                self._save_memory(session_id, content, importance, category)
                retained += 1
            elif importance >= 40:
                summary = self._extract_summary(content)
                self._save_memory(session_id, summary, importance, category)
                summarized += 1
            else:
                discarded += 1

        return {"retained": retained, "summarized": summarized, "discarded": discarded}

    def _extract_summary(self, content: str) -> str:
        if len(content) <= 50:
            return content
        for sep in ["。", "！", "？", ".", "!", "?", "\n"]:
            idx = content.find(sep)
            if 10 <= idx <= 50:
                return content[: idx + 1]
        return content[:50] + "..."

    def _save_memory(self, session_id: str, content: str, importance: int, category: str):
        entry_id = uuid.uuid4().hex[:12]
        db = SessionLocal()
        try:
            entry = MemoryEntry(
                id=entry_id,
                session_id=session_id,
                content=encrypt(content),
                importance=importance,
                category=category,
                timestamp=datetime.now(timezone.utc),
            )
            db.add(entry)
            db.commit()

            if self._vector_store:
                try:
                    self._vector_store.store(
                        entry_id=entry_id,
                        content=content,
                        metadata={"session_id": session_id, "importance": importance, "category": category},
                    )
                except Exception as e:
                    logging.warning("[降级] vector_store.store 失败: %s", e)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
