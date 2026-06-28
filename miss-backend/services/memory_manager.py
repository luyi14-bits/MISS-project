from datetime import datetime, timezone
from database import SessionLocal
from models.message import Message as MessageModel
from models.session import Session
from models.memory import MemoryEntry as MemoryEntryModel
from config import config
from .crypto import encrypt as _encrypt, decrypt as _decrypt


class ConversationStore:
    def ensure_session(self, session_id: str):
        db = SessionLocal()
        try:
            existing = db.query(Session).filter(Session.id == session_id).first()
            if not existing:
                db.add(Session(id=session_id, title="新对话"))
                db.commit()
        finally:
            db.close()

    def add_message(self, session_id: str, role: str, content: str):
        db = SessionLocal()
        try:
            self.ensure_session(session_id)
            msg = MessageModel(
                session_id=session_id,
                role=role,
                content=_encrypt(content),
                timestamp=datetime.now(timezone.utc),
            )
            db.add(msg)
            db.query(Session).filter(Session.id == session_id).update(
                {"updated_at": datetime.now(timezone.utc)}
            )
            db.commit()
            if role == "user" and self.get_message_count(session_id) <= 2:
                self._auto_title(session_id, content)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def _auto_title(self, session_id: str, first_message: str):
        title = first_message[:20]
        if len(first_message) > 20:
            title += "…"
        db = SessionLocal()
        try:
            db.query(Session).filter(Session.id == session_id).update({"title": title})
            db.commit()
        finally:
            db.close()

    def get_window(self, session_id: str, n: int = 20) -> list[dict]:
        n = n or config.conversation_window_size
        db = SessionLocal()
        try:
            rows = (
                db.query(MessageModel)
                .filter(MessageModel.session_id == session_id)
                .order_by(MessageModel.timestamp.desc())
                .limit(n)
                .all()
            )
            rows.reverse()
            return [{"role": r.role, "content": _decrypt(r.content)} for r in rows]
        finally:
            db.close()

    def get_overflow_messages(self, session_id: str, window_n: int = 20) -> list[dict]:
        db = SessionLocal()
        try:
            total = (
                db.query(MessageModel)
                .filter(MessageModel.session_id == session_id)
                .count()
            )
            if total <= window_n:
                return []
            skip = total - window_n
            rows = (
                db.query(MessageModel)
                .filter(MessageModel.session_id == session_id)
                .order_by(MessageModel.timestamp.asc())
                .limit(skip)
                .all()
            )
            return [
                {"id": r.id, "role": r.role, "content": _decrypt(r.content), "timestamp": r.timestamp.isoformat() if r.timestamp else None}
                for r in rows
            ]
        finally:
            db.close()

    def get_message_count(self, session_id: str) -> int:
        db = SessionLocal()
        try:
            return (
                db.query(MessageModel)
                .filter(MessageModel.session_id == session_id)
                .count()
            )
        finally:
            db.close()

    def list_sessions(self) -> list[dict]:
        db = SessionLocal()
        try:
            rows = db.query(Session).order_by(Session.updated_at.desc()).all()
            return [
                {
                    "id": r.id,
                    "title": r.title,
                    "message_count": self.get_message_count(r.id),
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                }
                for r in rows
            ]
        finally:
            db.close()

    def recall(self, session_id: str, query: str, top_k: int = 5) -> list[dict]:
        return []
