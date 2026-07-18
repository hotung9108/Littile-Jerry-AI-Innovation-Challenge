"""
Lưu trữ KnowledgeItem.

Mặc định dùng bộ nhớ tạm (in-memory) — chạy được ngay, không cần setup gì.
Nếu đã cấu hình DATABASE_URL (Postgres), tự động lưu song song vào DB để
giữ lịch sử lâu dài, tìm kiếm qua nhiều lần ingest thay vì mất khi restart.

Đây là nơi DUY NHẤT các route gọi vào để đọc/ghi KnowledgeItem — routes
không cần biết đang chạy in-memory hay có DB phía sau.
"""
from typing import List, Optional
from datetime import datetime

from app.knowledge_models import KnowledgeItem
from app.config import settings

# --- Bộ nhớ tạm, luôn hoạt động dù có DB hay không ---
_MEMORY_STORE: List[KnowledgeItem] = []


def _db_available() -> bool:
    return bool(settings.DATABASE_URL)


def save_items(items: List[KnowledgeItem]) -> List[KnowledgeItem]:
    global _MEMORY_STORE
    _MEMORY_STORE.extend(items)

    if _db_available():
        from app.db import get_session_factory
        from app.db_models import KnowledgeItemRecord

        SessionLocal = get_session_factory()
        with SessionLocal() as db:
            records = []
            for item in items:
                record = KnowledgeItemRecord(
                    type=item.type,
                    summary=item.summary,
                    owner=item.owner,
                    team=item.team,
                    project=item.project,
                    status=item.status,
                    related_to=item.related_to,
                    source=item.source,
                    source_ref=item.source_ref,
                    channel_or_doc=item.channel_or_doc,
                    created_at=item.created_at,
                    extracted_at=item.extracted_at,
                )
                db.add(record)
                records.append(record)
            db.commit()
            for record in records:
                db.refresh(record)
            # Gán lại id từ DB vào object trả về cho người gọi
            for item, record in zip(items, records):
                item.id = record.id

    return items


def list_items(
    project: Optional[str] = None,
    team: Optional[str] = None,
    type_: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 200,
) -> List[KnowledgeItem]:
    if _db_available():
        from app.db import get_session_factory
        from app.db_models import KnowledgeItemRecord

        SessionLocal = get_session_factory()
        with SessionLocal() as db:
            query = db.query(KnowledgeItemRecord)
            if project:
                query = query.filter(KnowledgeItemRecord.project == project)
            if team:
                query = query.filter(KnowledgeItemRecord.team == team)
            if type_:
                query = query.filter(KnowledgeItemRecord.type == type_)
            if status:
                query = query.filter(KnowledgeItemRecord.status == status)
            records = query.order_by(KnowledgeItemRecord.created_at.desc()).limit(limit).all()
            return [
                KnowledgeItem(
                    id=r.id,
                    type=r.type,
                    summary=r.summary,
                    owner=r.owner,
                    team=r.team,
                    project=r.project,
                    status=r.status,
                    related_to=r.related_to or [],
                    source=r.source,
                    source_ref=r.source_ref,
                    channel_or_doc=r.channel_or_doc,
                    created_at=r.created_at,
                    extracted_at=r.extracted_at,
                )
                for r in records
            ]

    # In-memory fallback
    results = _MEMORY_STORE
    if project:
        results = [i for i in results if i.project == project]
    if team:
        results = [i for i in results if i.team == team]
    if type_:
        results = [i for i in results if i.type == type_]
    if status:
        results = [i for i in results if i.status == status]
    return sorted(results, key=lambda i: i.created_at, reverse=True)[:limit]


def clear_memory_store():
    """Chỉ dùng cho test/demo — xoá dữ liệu mock đang lưu tạm trong bộ nhớ."""
    global _MEMORY_STORE
    _MEMORY_STORE = []
