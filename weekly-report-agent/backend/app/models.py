"""
Định nghĩa cấu trúc dữ liệu (schema) dùng chung cho toàn bộ hệ thống.
Mọi nguồn dữ liệu (mock hoặc Jira thật) đều phải được chuẩn hóa
về đúng các schema này trước khi đưa vào Agent workflow.
"""
from datetime import date as Date
from typing import Optional, List
from pydantic import BaseModel, Field


class DailyReportItem(BaseModel):
    """Một công việc (issue/ticket) được ghi nhận trong báo cáo ngày."""
    issue_key: str = Field(..., description="Mã ticket, vd: PROJ-101")
    title: str
    assignee: str
    project: str
    issue_type: str = Field(..., description="Task | Bug | Story | Decision")
    status: str = Field(..., description="To Do | In Progress | Done | Blocked")
    priority: str = Field(default="Medium", description="Low | Medium | High | Critical")
    story_points: Optional[float] = None
    date: Date
    comment: Optional[str] = Field(
        default=None, description="Ghi chú/cập nhật trong ngày, có thể chứa khó khăn/quyết định"
    )
    blocker: Optional[str] = Field(default=None, description="Mô tả khó khăn/vướng mắc nếu có")
    decision: Optional[str] = Field(default=None, description="Quyết định được đưa ra nếu có")
    labels: List[str] = Field(
        default_factory=list,
        description="Nhãn Jira gắn trên issue, vd: ['blocker'], ['decision']",
    )


class DailyReport(BaseModel):
    """Toàn bộ các item của một ngày."""
    date: Date
    items: List[DailyReportItem]


class WeeklyReportSection(BaseModel):
    title: str
    bullets: List[str]


class WeeklyReport(BaseModel):
    id: Optional[int] = Field(default=None, description="ID trong database (None nếu chưa lưu)")
    week_start: Date
    week_end: Date
    source: str = Field(..., description="mock | jira")
    assignee_filter: Optional[str] = Field(default=None, description="Lọc theo thành viên (nếu có)")
    project_filter: Optional[str] = Field(default=None, description="Lọc theo dự án (nếu có)")
    highlights: List[str] = Field(default_factory=list, description="1. Kết quả nổi bật")
    completed: List[str] = Field(default_factory=list, description="2. Công việc đã hoàn thành")
    in_progress: List[str] = Field(default_factory=list, description="3. Công việc đang thực hiện")
    blockers: List[str] = Field(default_factory=list, description="4. Khó khăn")
    decisions: List[str] = Field(default_factory=list, description="5. Quyết định")
    next_steps: List[str] = Field(default_factory=list, description="6. Công việc tiếp theo")
    raw_stats: dict = Field(default_factory=dict, description="Số liệu thống kê thô để tham khảo")
