"""
Onboarding Assistant.

Tạo bản tóm tắt kiến thức nền cho tình nguyện viên/nhân sự mới khi tham gia
một dự án — thay vì phải hỏi lại từng người hoặc đọc lại toàn bộ lịch sử
trò chuyện/tài liệu, hệ thống tự tổng hợp: quyết định quan trọng, khó khăn
đang tồn tại, việc đang cần làm, và những người chủ chốt nên liên hệ.
"""
from typing import List

from app.knowledge_models import KnowledgeItem, OnboardingBrief
from app import knowledge_store
from app.llm_client import chat_json, is_configured, LLMNotConfigured


def _rule_based_summary_line(items: List[KnowledgeItem]) -> str:
    if not items:
        return "Chưa có nhiều dữ liệu được ghi nhận cho dự án này."
    projects = {i.project for i in items if i.project}
    return (
        f"Dự án đang có {len(items)} mẩu tri thức được ghi nhận"
        + (f", liên quan tới: {', '.join(sorted(projects))}." if projects else ".")
    )


_SYSTEM_PROMPT = (
    "Bạn là trợ lý onboarding cho tình nguyện viên/nhân sự mới của một tổ chức "
    "phi lợi nhuận. Dựa vào danh sách knowledge item (JSON), viết một đoạn tóm tắt "
    "ngắn gọn (3-4 câu) bằng tiếng Việt, thân thiện, giúp người mới nắm bối cảnh "
    "nhanh nhất khi tham gia dự án.\n\n"
    'CHỈ trả về JSON: {"summary": "..."}'
)


def generate_onboarding_brief(project: str = None) -> OnboardingBrief:
    items = knowledge_store.list_items(project=project, limit=500)

    decisions = [i.summary for i in items if i.type == "decision"][:8]
    blockers = [i.summary for i in items if i.type == "blocker" and i.status == "open"][:8]
    actions = [i.summary for i in items if i.type == "action_item" and i.status == "open"][:8]
    people = sorted({i.owner for i in items if i.owner})[:10]

    summary = _rule_based_summary_line(items)
    if is_configured() and items:
        try:
            import json

            payload = json.dumps([i.model_dump(mode="json") for i in items], ensure_ascii=False)
            parsed = chat_json(_SYSTEM_PROMPT, payload)
            summary = parsed.get("summary", summary)
        except (LLMNotConfigured, Exception):
            pass

    return OnboardingBrief(
        project=project,
        summary=summary,
        key_decisions=decisions,
        open_blockers=blockers,
        active_action_items=actions,
        key_people=people,
    )
