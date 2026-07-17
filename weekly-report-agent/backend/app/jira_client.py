"""
Adapter kết nối Jira thật (Jira Cloud REST API v3).

Khi sẵn sàng dùng dữ liệu thật, set biến môi trường:
  DATA_SOURCE=jira
  JIRA_URL=https://your-domain.atlassian.net
  JIRA_EMAIL=your-email@company.com
  JIRA_API_TOKEN=xxxx   (tạo tại https://id.atlassian.com/manage-profile/security/api-tokens)
  JIRA_PROJECT_KEY=PROJ

Client này trả về đúng cấu trúc DailyReport/DailyReportItem như mock_data.py,
nên phần Agent workflow (normalizer/analyzer/summarizer) không cần thay đổi gì.
"""
from datetime import date, timedelta
from typing import List, Optional

import requests
from requests.auth import HTTPBasicAuth

from app.config import settings
from app.models import DailyReport, DailyReportItem

# Map trạng thái Jira -> trạng thái chuẩn hóa nội bộ
STATUS_MAP = {
    "To Do": "To Do",
    "Backlog": "To Do",
    "In Progress": "In Progress",
    "In Review": "In Progress",
    "Done": "Done",
    "Closed": "Done",
    "Blocked": "Blocked",
    "On Hold": "Blocked",
}


class JiraClient:
    def __init__(self):
        if not (settings.JIRA_URL and settings.JIRA_EMAIL and settings.JIRA_API_TOKEN):
            raise RuntimeError(
                "Thiếu cấu hình Jira. Vui lòng đặt JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN trong .env"
            )
        self.base_url = settings.JIRA_URL.rstrip("/")
        self.auth = HTTPBasicAuth(settings.JIRA_EMAIL, settings.JIRA_API_TOKEN)
        self.headers = {"Accept": "application/json"}

    def _search_issues(self, jql: str, fields: Optional[List[str]] = None) -> list:
        url = f"{self.base_url}/rest/api/3/search"
        fields = fields or [
            "summary", "assignee", "status", "priority", "issuetype",
            "project", "updated", "customfield_10016",  # story points (tuỳ workspace)
            "comment",
        ]
        params = {"jql": jql, "fields": ",".join(fields), "maxResults": 100}
        resp = requests.get(url, headers=self.headers, params=params, auth=self.auth, timeout=30)
        resp.raise_for_status()
        return resp.json().get("issues", [])

    def _issue_to_item(self, issue: dict, day: date) -> DailyReportItem:
        f = issue["fields"]
        status_name = f.get("status", {}).get("name", "To Do")
        status = STATUS_MAP.get(status_name, "In Progress")

        comment_text = None
        blocker = None
        decision = None
        comments = f.get("comment", {}).get("comments", [])
        if comments:
            last = comments[-1]
            # Nội dung comment Jira ở dạng Atlassian Document Format (ADF); lấy text đơn giản
            try:
                comment_text = " ".join(
                    part.get("text", "")
                    for block in last.get("body", {}).get("content", [])
                    for part in block.get("content", [])
                    if "text" in part
                )
            except Exception:
                comment_text = None

            if comment_text:
                lowered = comment_text.lower()
                if any(k in lowered for k in ["block", "chặn", "vướng", "khó khăn"]):
                    blocker = comment_text
                elif any(k in lowered for k in ["quyết định", "decide", "decision"]):
                    decision = comment_text

        return DailyReportItem(
            issue_key=issue["key"],
            title=f.get("summary", ""),
            assignee=(f.get("assignee") or {}).get("displayName", "Unassigned"),
            project=f.get("project", {}).get("key", settings.JIRA_PROJECT_KEY),
            issue_type=f.get("issuetype", {}).get("name", "Task"),
            status=status,
            priority=(f.get("priority") or {}).get("name", "Medium"),
            story_points=f.get("customfield_10016"),
            date=day,
            comment=comment_text,
            blocker=blocker,
            decision=decision,
        )

    def fetch_daily_reports(self, days: int = 5) -> List[DailyReport]:
        """
        Lấy các issue được cập nhật trong `days` ngày gần nhất của project
        và nhóm lại theo từng ngày để tạo danh sách DailyReport.
        """
        today = date.today()
        start = today - timedelta(days=days - 1)
        jql = (
            f'project = "{settings.JIRA_PROJECT_KEY}" '
            f'AND updated >= "{start.isoformat()}" ORDER BY updated ASC'
        )
        issues = self._search_issues(jql)

        reports_by_day = {today - timedelta(days=i): [] for i in range(days)}
        for issue in issues:
            updated_str = issue["fields"].get("updated", "")
            try:
                updated_day = date.fromisoformat(updated_str[:10])
            except ValueError:
                updated_day = today
            if updated_day not in reports_by_day:
                continue
            reports_by_day[updated_day].append(self._issue_to_item(issue, updated_day))

        return [
            DailyReport(date=d, items=items)
            for d, items in sorted(reports_by_day.items())
        ]
