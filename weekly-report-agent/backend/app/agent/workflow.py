"""
Orchestrator: ghép các bước của Agent workflow lại thành 1 pipeline duy nhất.

    fetch (mock hoặc jira) -> normalize -> analyze -> summarize -> WeeklyReport

Đây là điểm duy nhất cần sửa khi chuyển từ mock sang dữ liệu Jira thật:
chỉ cần đổi nguồn fetch, các bước còn lại giữ nguyên vì đã được chuẩn hóa
qua cùng một schema (DailyReport / DailyReportItem).
"""
from datetime import date, timedelta
from typing import List

from app.mock_data import generate_mock_daily_reports
from app.models import DailyReport, WeeklyReport
from app.agent.normalizer import normalize_reports
from app.agent.analyzer import analyze_items
from app.agent.summarizer import summarize


class WeeklyReportAgent:
    def run(
        self,
        source: str = "mock",
        days: int = 5,
        assignee: str = None,
        project: str = None,
    ) -> WeeklyReport:
        raw_reports: List[DailyReport] = self._fetch(source, days)

        # Bước 1: chuẩn hóa
        items = normalize_reports(raw_reports)

        # Lọc theo thành viên/dự án nếu có nhiều team dùng chung hệ thống
        if assignee:
            items = [i for i in items if i.assignee.lower() == assignee.lower()]
        if project:
            items = [i for i in items if i.project.lower() == project.lower()]

        # Bước 2: phân tích
        buckets = analyze_items(items)

        # Bước 3: tổng hợp thành báo cáo dạng văn bản
        summary = summarize(buckets)

        week_end = date.today()
        week_start = week_end - timedelta(days=days - 1)

        return WeeklyReport(
            week_start=week_start,
            week_end=week_end,
            source=source,
            assignee_filter=assignee,
            project_filter=project,
            highlights=summary["highlights"],
            completed=summary["completed"],
            in_progress=summary["in_progress"],
            blockers=summary["blockers"],
            decisions=summary["decisions"],
            next_steps=summary["next_steps"],
            raw_stats={
                "total_items": len(items),
                "completed_count": len(buckets["completed"]),
                "in_progress_count": len(buckets["in_progress"]),
                "blockers_count": len(buckets["blockers"]),
                "decisions_count": len(buckets["decisions"]),
            },
        )

    def _fetch(self, source: str, days: int) -> List[DailyReport]:
        if source == "mock":
            return generate_mock_daily_reports(days=days)
        elif source == "jira":
            from app.jira_client import JiraClient  # import trễ để tránh lỗi khi thiếu cấu hình
            return JiraClient().fetch_daily_reports(days=days)
        else:
            raise ValueError(f"Nguồn dữ liệu không hợp lệ: {source}")
