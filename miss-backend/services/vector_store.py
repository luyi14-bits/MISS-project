# Copyright (C) 2026  MISS Project Contributors
# SPDX-License-Identifier: AGPL-3.0-or-later
# This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
import json
import logging
from datetime import datetime, timezone
from config import config, get_api_key, get_base_url
from database import SessionLocal
from models.memory import MemoryEntry as MemoryEntryModel
from .crypto import decrypt


class VectorMemoryStore:
    COLLECTION_NAME = "miss_memories"

    def __init__(self, api_key: str | None = None):
        self._key = api_key or get_api_key()
        self._chroma_client = None
        self._collection = None
        self._disabled = False
        try:
            from chromadb import PersistentClient
            self._chroma_client = PersistentClient(path=config.vector_db_path)
        except Exception as e:
            logging.warning("[VectorMemoryStore] chromadb 不可用，向量功能已禁用: %s", e)
            self._disabled = True

    @property
    def collection(self):
        if self._disabled:
            return None
        if self._collection is None:
            from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
            ef = None
            if self._key:
                kwargs = dict(api_key=self._key, model_name="text-embedding-3-small")
                base_url = get_base_url()
                if base_url:
                    kwargs["api_base"] = base_url
                ef = OpenAIEmbeddingFunction(**kwargs)
            self._collection = self._chroma_client.get_or_create_collection(
                name=self.COLLECTION_NAME, embedding_function=ef,
            )
        return self._collection

    def store(self, entry_id: str, content: str, metadata: dict | None = None):
        if self._disabled or not self.collection:
            return
        meta = metadata or {}
        self.collection.add(
            ids=[entry_id],
            documents=[content],
            metadatas=[{**meta, "stored_at": datetime.now(timezone.utc).isoformat()}],
        )

    def recall(self, query: str, top_k: int = 5) -> list[dict]:
        if self._disabled or not self.collection:
            return []
        results = self.collection.query(query_texts=[query], n_results=top_k)
        entries = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                raw = results["documents"][0][i] if results["documents"] else ""
                entry = {"id": doc_id, "content": decrypt(raw)}
                if results["metadatas"] and results["metadatas"][0]:
                    entry.update(results["metadatas"][0][i] or {})
                if results["distances"]:
                    entry["distance"] = results["distances"][0][i]
                entries.append(entry)
        return entries

    def sync_from_db(self, session_id: str | None = None):
        db = SessionLocal()
        try:
            query = db.query(MemoryEntryModel)
            if session_id:
                query = query.filter(MemoryEntryModel.session_id == session_id)
            rows = query.all()

            ids = []
            documents = []
            metadatas = []
            for r in rows:
                if not r.content:
                    continue
                ids.append(r.id)
                documents.append(decrypt(r.content) if r.content else "")
                metadatas.append({
                    "session_id": r.session_id,
                    "importance": r.importance,
                    "category": r.category,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                })

            if ids:
                self.collection.add(ids=ids, documents=documents, metadatas=metadatas)

            self._save_embedding_to_db(rows)
        finally:
            db.close()

    def _save_embedding_to_db(self, rows):
        try:
            stored = self.collection.get(ids=[r.id for r in rows], include=["embeddings"])
            db = SessionLocal()
            try:
                for i, row in enumerate(rows):
                    if stored["embeddings"] and stored["embeddings"][i]:
                        emb = stored["embeddings"][i]
                        db.query(MemoryEntryModel).filter(
                            MemoryEntryModel.id == row.id
                        ).update({"embedding": json.dumps(emb)})
                db.commit()
            finally:
                db.close()
        except Exception as e:
            logging.warning("[向量库] 回写embedding失败: %s", e)

    def recall_with_threshold(self, query: str, top_k: int = 5, threshold: float = 0.5) -> list[dict]:
        if self._disabled or not self.collection:
            return []
        results = self.collection.query(query_texts=[query], n_results=top_k, include=["distances"])
        entries = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                dist = results["distances"][0][i] if results["distances"] else 0
                if dist > threshold:
                    continue
                entry = {"id": doc_id, "content": results["documents"][0][i] if results["documents"] else "", "distance": dist}
                if results["metadatas"] and results["metadatas"][0]:
                    entry.update(results["metadatas"][0][i] or {})
                entries.append(entry)
        return entries

    def remove(self, entry_id: str):
        if self._disabled or not self.collection:
            return
        self.collection.delete(ids=[entry_id])

    def count(self) -> int:
        return self.collection.count()

    def age(self, max_age_days: int = 30) -> dict:
        db = SessionLocal()
        try:
            from datetime import timedelta
            cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
            old_entries = (
                db.query(MemoryEntryModel)
                .filter(MemoryEntryModel.timestamp < cutoff)
                .all()
            )
            deleted = 0
            decayed = 0
            for entry in old_entries:
                if entry.importance < 40:
                    db.delete(entry)
                    try:
                        self.remove(entry.id)
                    except Exception as e:
                        logging.warning("[降级] age 清理失败: %s", e)
                    deleted += 1
                else:
                    new_imp = max(0, entry.importance - 10)
                    entry.importance = new_imp
                    if new_imp == 0:
                        db.delete(entry)
                        try:
                            self.remove(entry.id)
                        except Exception:
                            logging.warning("[向量库] remove失败: %s", entry.id)
                    decayed += 1
            db.commit()
            return {"deleted": deleted, "decayed": decayed}
        finally:
            db.close()
