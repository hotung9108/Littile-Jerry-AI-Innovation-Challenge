"""
Schema dùng chung cho "Organizational Brain" — lớp tri thức tổ chức.

Luồng xử lý:
    RawEvent (thô, từ Slack/Email/Meeting/GDocs/Task tool)
        -> extractor (LLM hoặc rule-based)
        -> KnowledgeItem (đã trích xuất: decision / action_item / blocker / relationship / fact)
        -> lưu trữ + index để tìm kiếm (search_knowledge)
        -> risk_monitor quét KnowledgeItem để phát hiện rủi ro/phụ thuộc
"""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field

SourceType = Literal["slack", "email", "meeting", "gdocs", "tasks"]
KnowledgeType = Literal["decision", "action_item", "blocker", "relationship", "fact"]


class RawEvent(BaseModel):
    """Một đơn vị dữ liệu thô lấy về từ 1 kênh làm việc, trước khi được AI hiểu."""
    source: SourceType
    source_ref: str = Field(..., description="ID gốc: message ts, email id, doc id, meeting id...")
    channel_or_doc: str = Field(..., description="Kênh Slack, tiêu đề doc, tên cuộc họp, subject email...")
    author: str
    team: Optional[str] = Field(default=None, description="Team/nhóm liên quan, nếu xác định được")
    project: Optional[str] = Field(default=None, description="Dự án liên quan, nếu xác định được")
    timestamp: datetime
    content: str = Field(..., description="Nội dung thô: tin nhắn, đoạn transcript, đoạn văn bản doc...")


class KnowledgeItem(BaseModel):
    """Một mẩu tri thức đã được AI trích xuất từ RawEvent."""
    id: Optional[int] = None
    type: KnowledgeType
    summary: str = Field(..., description="Tóm tắt ngắn gọn, súc tích")
    owner: Optional[str] = Field(default=None, description="Người chịu trách nhiệm / liên quan chính")
    team: Optional[str] = None
    project: Optional[str] = None
    status: str = Field(default="open", description="open | in_progress | resolved | stale")
    related_to: List[str] = Field(
        default_factory=list, description="issue_key/doc_id/knowledge item khác có liên quan"
    )
    source: SourceType
    source_ref: str
    channel_or_doc: str
    created_at: datetime
    extracted_at: datetime = Field(default_factory=datetime.utcnow)


class SearchResult(BaseModel):
    query: str
    answer: Optional[str] = Field(default=None, description="Câu trả lời tổng hợp (nếu có LLM)")
    items: List[KnowledgeItem] = Field(default_factory=list, description="Các knowledge item liên quan nhất")


class RiskAlert(BaseModel):
    level: Literal["info", "warning", "critical"]
    title: str
    description: str
    related_items: List[KnowledgeItem] = Field(default_factory=list)
    suggested_action: str


class OnboardingBrief(BaseModel):
    project: Optional[str] = None
    summary: str
    key_decisions: List[str] = Field(default_factory=list)
    open_blockers: List[str] = Field(default_factory=list)
    active_action_items: List[str] = Field(default_factory=list)
    key_people: List[str] = Field(default_factory=list)
