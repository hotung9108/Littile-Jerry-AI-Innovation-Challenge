"""
Bước 1 của Agent workflow: CHUẨN HÓA dữ liệu.

Nhận danh sách DailyReport (thô, có thể đến từ mock hoặc Jira thật)
và trả về danh sách DailyReportItem đã được làm sạch, gộp lại,
loại trùng lặp — sẵn sàng cho bước phân tích (analyzer).
"""
from typing import List

from app.models import DailyReport, DailyReportItem

STATUS_ALIASES = {
    "todo": "To Do",
    "to do": "To Do",
    "backlog": "To Do",
    "doing": "In Progress",
    "in progress": "In Progress",
    "in review": "In Progress",
    "done": "Done",
    "closed": "Done",
    "resolved": "Done",
    "blocked": "Blocked",
    "on hold": "Blocked",
}


def _normalize_status(status: str) -> str:
    return STATUS_ALIASES.get(status.strip().lower(), status.strip().title())


def normalize_reports(reports: List[DailyReport]) -> List[DailyReportItem]:
    """Gộp toàn bộ các ngày thành một danh sách item duy nhất, đã chuẩn hóa."""
    all_items: List[DailyReportItem] = []
    seen_keys_per_day = set()

    for report in reports:
        for item in report.items:
            dedup_key = (item.issue_key, item.date, item.status)
            if dedup_key in seen_keys_per_day:
                continue
            seen_keys_per_day.add(dedup_key)

            item.status = _normalize_status(item.status)
            item.title = item.title.strip()
            if item.comment:
                item.comment = item.comment.strip()

            all_items.append(item)

    return all_items
