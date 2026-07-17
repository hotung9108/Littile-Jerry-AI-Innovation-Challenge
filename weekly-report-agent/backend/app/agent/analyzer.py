"""
Bước 2 của Agent workflow: PHÂN TÍCH dữ liệu đã chuẩn hóa.

Từ danh sách DailyReportItem của cả tuần, xác định:
- Công việc đã hoàn thành (status cuối tuần = Done)
- Công việc đang thực hiện (status cuối tuần = In Progress / To Do)
- Khó khăn / vướng mắc (item có blocker, hoặc status = Blocked)
- Quyết định đã đưa ra (item có decision)
- Kết quả nổi bật (ưu tiên cao/critical đã Done, hoặc story point lớn)
"""
from collections import defaultdict
from typing import Dict, List

from app.models import DailyReportItem


def analyze_items(items: List[DailyReportItem]) -> Dict[str, List[DailyReportItem]]:
    # Lấy trạng thái MỚI NHẤT của từng issue trong tuần (theo ngày gần nhất)
    latest_by_issue: Dict[str, DailyReportItem] = {}
    for item in sorted(items, key=lambda i: i.date):
        latest_by_issue[item.issue_key] = item

    completed: List[DailyReportItem] = []
    in_progress: List[DailyReportItem] = []
    blockers: List[DailyReportItem] = []
    decisions: List[DailyReportItem] = []
    highlights: List[DailyReportItem] = []

    # Blocker và decision có thể xuất hiện ở bất kỳ ngày nào trong tuần,
    # không chỉ ở bản ghi mới nhất -> quét toàn bộ items.
    for item in items:
        if item.blocker:
            blockers.append(item)
        if item.decision:
            decisions.append(item)

    for issue_key, item in latest_by_issue.items():
        if item.status == "Done":
            completed.append(item)
            if item.priority in ("High", "Critical") or (item.story_points or 0) >= 5:
                highlights.append(item)
        elif item.status in ("In Progress", "To Do"):
            in_progress.append(item)
        elif item.status == "Blocked" and item not in blockers:
            blockers.append(item)

    # Loại trùng theo issue_key cho từng nhóm, giữ thứ tự
    def _dedup(seq: List[DailyReportItem]) -> List[DailyReportItem]:
        seen = set()
        result = []
        for i in seq:
            if i.issue_key not in seen:
                seen.add(i.issue_key)
                result.append(i)
        return result

    return {
        "highlights": _dedup(highlights),
        "completed": _dedup(completed),
        "in_progress": _dedup(in_progress),
        "blockers": _dedup(blockers),
        "decisions": _dedup(decisions),
    }
