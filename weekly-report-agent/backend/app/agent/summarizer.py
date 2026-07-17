"""
Bước 3 của Agent workflow: TỔNG HỢP thành báo cáo tuần dạng ngôn ngữ tự nhiên.

LLM_PROVIDER=groq       -> dùng Groq (Llama qua API tương thích OpenAI)
LLM_PROVIDER=anthropic  -> dùng Claude (Anthropic API)
LLM_PROVIDER=none       -> dùng bộ tóm tắt rule-based (templated), không cần LLM

Nếu gọi LLM lỗi (sai key, hết quota, timeout...) hệ thống tự động fallback
về rule-based để không làm sập luồng tạo báo cáo.
"""
import json
from typing import Dict, List

from app.config import settings
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

    # Công việc tiếp theo: suy ra từ các việc đang dở dang + việc bị chặn cần giải quyết
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
    raw_data = {
        key: [item.model_dump(mode="json") for item in items]
        for key, items in buckets.items()
    }
    return json.dumps(raw_data, ensure_ascii=False)


def _parse_llm_json(text: str, buckets: Dict[str, List[DailyReportItem]]) -> Dict[str, List[str]]:
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        parsed = json.loads(text)
        # Đảm bảo đủ 6 khóa, phòng khi model bỏ sót
        for key in ["highlights", "completed", "in_progress", "blockers", "decisions", "next_steps"]:
            parsed.setdefault(key, [])
        return parsed
    except json.JSONDecodeError:
        # Nếu LLM trả về sai định dạng, fallback về rule-based để không làm hỏng luồng
        return _rule_based_summary(buckets)


def _anthropic_summary(buckets: Dict[str, List[DailyReportItem]]) -> Dict[str, List[str]]:
    """Dùng Claude (Anthropic API) để viết lại báo cáo súc tích, chuyên nghiệp hơn."""
    import anthropic

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    response = client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=2000,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _buckets_to_json(buckets)}],
    )

    text = "".join(block.text for block in response.content if block.type == "text")
    return _parse_llm_json(text, buckets)


def _groq_summary(buckets: Dict[str, List[DailyReportItem]]) -> Dict[str, List[str]]:
    """Dùng Groq (Llama/Mixtral... qua API tương thích OpenAI) để viết lại báo cáo."""
    import requests

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _buckets_to_json(buckets)},
        ],
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    text = data["choices"][0]["message"]["content"]
    return _parse_llm_json(text, buckets)


def summarize(buckets: Dict[str, List[DailyReportItem]]) -> Dict[str, List[str]]:
    provider = settings.LLM_PROVIDER

    try:
        if provider == "groq" and settings.GROQ_API_KEY:
            return _groq_summary(buckets)
        if provider == "anthropic" and settings.ANTHROPIC_API_KEY:
            return _anthropic_summary(buckets)
    except Exception:
        # Không để lỗi gọi LLM làm sập cả API -> fallback an toàn
        return _rule_based_summary(buckets)

    return _rule_based_summary(buckets)