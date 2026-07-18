"""
Bước 3 của Agent workflow: TỔNG HỢP thành báo cáo tuần dạng ngôn ngữ tự nhiên.

Dùng chung app/llm_client.py (Groq/Anthropic). Nếu chưa cấu hình LLM hoặc
gọi lỗi -> tự động fallback về rule-based để không làm sập luồng.
"""
from typing import Dict, List

from app.llm_client import chat_json, is_configured, LLMNotConfigured
from app.models import DailyReportItem


def _item_line(item: DailyReportItem, include_note: bool = True) -> str:
    line = f"[{item.issue_key}] {item.title} ({item.assignee})"
    if include_note and item.comment:
        line += f" — {item.comment}"
    return line


def _rule_based_summary(buckets: Dict[str, List[DailyReportItem]]) -> Dict[str, List[str]]:
    """Tóm tắt không cần LLM — ghép template tiếng Việt từ dữ liệu đã phân tích."""

    highlights = [
        f"Hoàn thành {i.title} (ưu tiên {i.priority}, {i.story_points or '?'} story point) — {i.assignee}"
        for i in buckets["highlights"]
    ] or ["Không có kết quả nổi bật đặc biệt trong tuần này."]

    completed = [_item_line(i, include_note=False) for i in buckets["completed"]] or [
        "Không có công việc nào được hoàn thành trong tuần."
    ]

    in_progress = [_item_line(i, include_note=False) for i in buckets["in_progress"]] or [
        "Không có công việc nào đang thực hiện."
    ]

    blockers = [
        f"[{i.issue_key}] {i.title} ({i.assignee}) — {i.blocker or i.comment or 'đang bị chặn'}"
        for i in buckets["blockers"]
    ] or ["Không ghi nhận khó khăn/vướng mắc đáng kể trong tuần."]

    decisions = [
        f"{i.decision} (liên quan {i.issue_key}, {i.assignee})" for i in buckets["decisions"]
    ] or ["Không có quyết định quan trọng nào được ghi nhận trong tuần."]

    next_steps = []
    for i in buckets["in_progress"]:
        next_steps.append(f"Tiếp tục {i.title} ({i.assignee})")
    for i in buckets["blockers"]:
        next_steps.append(f"Giải quyết vướng mắc cho {i.title} ({i.assignee})")
    if not next_steps:
        next_steps = ["Lên kế hoạch công việc cho tuần tới."]

    return {
        "highlights": highlights,
        "completed": completed,
        "in_progress": in_progress,
        "blockers": blockers,
        "decisions": decisions,
        "next_steps": next_steps,
    }


_SYSTEM_PROMPT = (
    "Bạn là trợ lý tổng hợp báo cáo công việc cho một đội kỹ thuật. "
    "Dựa trên dữ liệu JSON được cung cấp (đã được phân loại sẵn thành các nhóm: "
    "highlights, completed, in_progress, blockers, decisions), hãy viết lại thành "
    "các gạch đầu dòng SÚC TÍCH, RÕ RÀNG bằng tiếng Việt, giọng văn báo cáo công việc "
    "chuyên nghiệp. Đồng thời tự suy luận thêm mục 'next_steps' (công việc tiếp theo) "
    "dựa trên các việc đang thực hiện và các khó khăn cần giải quyết.\n\n"
    "CHỈ trả về JSON hợp lệ, không thêm text khác, đúng format:\n"
    '{"highlights": [...], "completed": [...], "in_progress": [...], '
    '"blockers": [...], "decisions": [...], "next_steps": [...]}\n'
    "Mỗi phần tử trong list là một chuỗi (string), không quá 25 từ."
)


def _buckets_to_json(buckets: Dict[str, List[DailyReportItem]]) -> str:
    import json

    raw_data = {
        key: [item.model_dump(mode="json") for item in items]
        for key, items in buckets.items()
    }
    return json.dumps(raw_data, ensure_ascii=False)


def summarize(buckets: Dict[str, List[DailyReportItem]]) -> Dict[str, List[str]]:
    if not is_configured():
        return _rule_based_summary(buckets)

    try:
        parsed = chat_json(_SYSTEM_PROMPT, _buckets_to_json(buckets))
        for key in ["highlights", "completed", "in_progress", "blockers", "decisions", "next_steps"]:
            parsed.setdefault(key, [])
        return parsed
    except (LLMNotConfigured, Exception):
        return _rule_based_summary(buckets)
