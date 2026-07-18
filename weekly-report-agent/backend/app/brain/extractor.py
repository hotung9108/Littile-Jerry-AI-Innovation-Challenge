"""
Extraction Agent: hiểu ngữ cảnh của từng RawEvent (tin nhắn Slack, email,
đoạn biên bản họp, đoạn Google Docs...) và trích xuất ra KnowledgeItem có
cấu trúc: decision / action_item / blocker / relationship / fact.

Có 2 chế độ:
- LLM (Groq/Anthropic, qua app/llm_client.py): hiểu ngữ cảnh tốt hơn, xử lý
  được câu văn tự nhiên phức tạp.
- Rule-based (fallback khi chưa cấu hình LLM): dò từ khóa tiếng Việt phổ biến
  ("quyết định", "chặn", "vướng mắc", "sẽ", "phụ trách"...) — độ chính xác
  thấp hơn nhưng đảm bảo hệ thống luôn chạy được, không phụ thuộc LLM.
"""
from typing import List
from datetime import datetime

from app.llm_client import chat_json, is_configured, LLMNotConfigured
from app.knowledge_models import RawEvent, KnowledgeItem

_DECISION_KEYWORDS = ["quyết định", "thống nhất", "chốt", "đồng ý chọn", "quyết"]
_BLOCKER_KEYWORDS = ["chưa nhận được", "chặn", "vướng mắc", "thiếu", "vượt dự trù", "quá tải", "chưa thể"]
_ACTION_KEYWORDS = ["sẽ", "phụ trách", "chịu trách nhiệm", "cần hoàn thiện", "đề nghị"]
_RELATIONSHIP_KEYWORDS = ["phụ thuộc vào", "liên quan đến", "cần phối hợp"]


def _rule_based_extract(event: RawEvent) -> KnowledgeItem:
    text = event.content.lower()

    if any(k in text for k in _RELATIONSHIP_KEYWORDS):
        item_type = "relationship"
    elif any(k in text for k in _BLOCKER_KEYWORDS):
        item_type = "blocker"
    elif any(k in text for k in _DECISION_KEYWORDS):
        item_type = "decision"
    elif any(k in text for k in _ACTION_KEYWORDS):
        item_type = "action_item"
    else:
        item_type = "fact"

    return KnowledgeItem(
        type=item_type,
        summary=event.content[:200],
        owner=event.author,
        team=event.team,
        project=event.project,
        status="open" if item_type in ("blocker", "action_item") else "resolved",
        related_to=[],
        source=event.source,
        source_ref=event.source_ref,
        channel_or_doc=event.channel_or_doc,
        created_at=event.timestamp,
    )


_SYSTEM_PROMPT = (
    "Bạn là AI phân tích tri thức tổ chức cho một tổ chức phi lợi nhuận (NPO). "
    "Với mỗi sự kiện thô (tin nhắn/email/biên bản họp/đoạn tài liệu) được cung cấp "
    "dưới dạng JSON, hãy phân loại thành đúng 1 trong 5 loại: "
    "decision (quyết định), action_item (việc cần làm, có người phụ trách), "
    "blocker (khó khăn/vướng mắc đang chặn tiến độ), "
    "relationship (mối phụ thuộc giữa các công việc/dự án), "
    "fact (thông tin/số liệu, không thuộc 4 loại trên).\n\n"
    "Viết lại `summary` súc tích bằng tiếng Việt (dưới 30 từ), giữ đúng ý gốc, "
    "không thêm thông tin bịa đặt. Nếu là action_item hoặc blocker, đặt status='open', "
    "ngược lại status='resolved'.\n\n"
    "CHỈ trả về JSON đúng format:\n"
    '{"type": "...", "summary": "...", "status": "open|resolved"}'
)


def _llm_extract(event: RawEvent) -> KnowledgeItem:
    import json

    user_content = json.dumps(
        {
            "source": event.source,
            "channel_or_doc": event.channel_or_doc,
            "author": event.author,
            "content": event.content,
        },
        ensure_ascii=False,
    )
    parsed = chat_json(_SYSTEM_PROMPT, user_content)

    return KnowledgeItem(
        type=parsed.get("type", "fact"),
        summary=parsed.get("summary", event.content[:200]),
        owner=event.author,
        team=event.team,
        project=event.project,
        status=parsed.get("status", "open"),
        related_to=[],
        source=event.source,
        source_ref=event.source_ref,
        channel_or_doc=event.channel_or_doc,
        created_at=event.timestamp,
    )


def extract_knowledge(events: List[RawEvent]) -> List[KnowledgeItem]:
    """Trích xuất KnowledgeItem cho một danh sách RawEvent."""
    use_llm = is_configured()
    items: List[KnowledgeItem] = []

    for event in events:
        if use_llm:
            try:
                items.append(_llm_extract(event))
                continue
            except (LLMNotConfigured, Exception):
                pass  # rơi xuống rule-based bên dưới
        items.append(_rule_based_extract(event))

    return items
