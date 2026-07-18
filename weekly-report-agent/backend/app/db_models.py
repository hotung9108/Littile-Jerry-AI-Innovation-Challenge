"""
ORM models (SQLAlchemy) — định nghĩa bảng lưu trong Postgres.

Chỉ được dùng nếu DATABASE_URL được cấu hình trong .env. Nếu không,
hệ thống vẫn chạy bình thường với bộ nhớ tạm (xem app/knowledge_store.py
và _STORE trong app/main.py).
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from sqlalchemy.sql import func

from app.db import Base


class WeeklyReportRecord(Base):
    __tablename__ = "weekly_reports"

    id = Column(Integer, primary_key=True, index=True)
    week_start = Column(DateTime, nullable=False)
    week_end = Column(DateTime, nullable=False)
    source = Column(String(20), nullable=False)
    assignee_filter = Column(String(100), nullable=True)
    project_filter = Column(String(200), nullable=True)

    highlights = Column(JSON, default=list)
    completed = Column(JSON, default=list)
    in_progress = Column(JSON, default=list)
    blockers = Column(JSON, default=list)
    decisions = Column(JSON, default=list)
    next_steps = Column(JSON, default=list)
    raw_stats = Column(JSON, default=dict)

    created_at = Column(DateTime, server_default=func.now())


class KnowledgeItemRecord(Base):
    __tablename__ = "knowledge_items"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(20), nullable=False, index=True)
    summary = Column(Text, nullable=False)
    owner = Column(String(100), nullable=True, index=True)
    team = Column(String(100), nullable=True, index=True)
    project = Column(String(200), nullable=True, index=True)
    status = Column(String(20), default="open", index=True)
    related_to = Column(JSON, default=list)

    source = Column(String(20), nullable=False)
    source_ref = Column(String(200), nullable=False)
    channel_or_doc = Column(String(300), nullable=True)

    created_at = Column(DateTime, nullable=False, index=True)
    extracted_at = Column(DateTime, server_default=func.now())
