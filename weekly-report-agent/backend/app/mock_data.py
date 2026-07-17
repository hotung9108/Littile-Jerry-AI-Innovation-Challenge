"""
Sinh dữ liệu MOCK mô phỏng báo cáo hằng ngày lấy từ Jira.
Dùng để phát triển/test Agent workflow trước khi nối API Jira thật.

Khi chuyển sang dữ liệu thật, chỉ cần thay lời gọi generate_mock_daily_reports()
bằng JiraClient.fetch_daily_reports() ở workflow.py — cấu trúc trả về
(DailyReport / DailyReportItem) giữ nguyên.
"""
import random
from datetime import date, timedelta
from typing import List

from app.models import DailyReport, DailyReportItem

ASSIGNEES = ["Minh", "Lan", "Huy", "Trang", "Khoa", "An"]
PROJECTS = ["PROJ"]
ISSUE_TYPES = ["Task", "Bug", "Story"]
STATUSES = ["To Do", "In Progress", "Done", "Blocked"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]

TASK_TITLES = [
    "Xây dựng API xác thực người dùng",
    "Tối ưu truy vấn database cho module báo cáo",
    "Sửa lỗi hiển thị sai định dạng ngày trên dashboard",
    "Thiết kế lại giao diện trang đăng nhập",
    "Viết unit test cho service thanh toán",
    "Tích hợp webhook thông báo Slack",
    "Refactor module xử lý hàng đợi (queue)",
    "Cấu hình CI/CD cho môi trường staging",
    "Khắc phục lỗi tràn bộ nhớ khi xử lý file lớn",
    "Bổ sung logging cho microservice thanh toán",
    "Xây dựng agent tổng hợp báo cáo tuần",
    "Chuẩn hóa dữ liệu đầu vào từ Jira",
    "Viết tài liệu API cho đối tác",
    "Kiểm thử hiệu năng hệ thống dưới tải cao",
    "Cập nhật thư viện bảo mật lên phiên bản mới",
]

BLOCKERS = [
    "Chờ team hạ tầng cấp quyền truy cập server staging",
    "Thiếu tài liệu API từ bên thứ ba",
    "Phát sinh xung đột dữ liệu chưa xác định được nguyên nhân",
    "Chờ phê duyệt thiết kế từ Product Owner",
    "Môi trường test không ổn định, cần được khắc phục",
]

DECISIONS = [
    "Quyết định dùng PostgreSQL thay vì MongoDB cho module báo cáo",
    "Thống nhất chuyển sang kiến trúc microservice cho phần thanh toán",
    "Chốt deadline release bản beta vào thứ Sáu tuần sau",
    "Quyết định tạm hoãn tính năng export PDF sang sprint sau",
    "Thống nhất quy trình code review bắt buộc 2 approvals",
]


def _random_item(issue_id: int, day: date) -> DailyReportItem:
    status = random.choices(STATUSES, weights=[15, 40, 35, 10])[0]
    issue_type = random.choice(ISSUE_TYPES)
    priority = random.choices(PRIORITIES, weights=[20, 40, 30, 10])[0]

    blocker = None
    decision = None
    comment = None

    if status == "Blocked":
        blocker = random.choice(BLOCKERS)
        comment = f"Bị chặn: {blocker}"
    elif random.random() < 0.12:
        decision = random.choice(DECISIONS)
        comment = f"Quyết định trong buổi trao đổi nhóm: {decision}"
    elif status == "Done":
        comment = "Đã hoàn thành và merge vào nhánh main."
    elif status == "In Progress":
        comment = "Đang triển khai, tiến độ ổn định."

    return DailyReportItem(
        issue_key=f"PROJ-{issue_id}",
        title=random.choice(TASK_TITLES),
        assignee=random.choice(ASSIGNEES),
        project=random.choice(PROJECTS),
        issue_type=issue_type,
        status=status,
        priority=priority,
        story_points=random.choice([1, 2, 3, 5, 8]),
        date=day,
        comment=comment,
        blocker=blocker,
        decision=decision,
    )


def generate_mock_daily_reports(days: int = 5, items_per_day: int = 6) -> List[DailyReport]:
    """
    Sinh danh sách DailyReport cho `days` ngày làm việc gần nhất
    (mặc định 5 ngày = 1 tuần làm việc), mỗi ngày `items_per_day` công việc.
    """
    reports: List[DailyReport] = []
    today = date.today()
    issue_id_counter = 100

    # Lấy `days` ngày gần nhất lùi về trước (bỏ qua random hoàn toàn theo thứ tự thời gian)
    for offset in range(days - 1, -1, -1):
        day = today - timedelta(days=offset)
        items = []
        for _ in range(items_per_day):
            issue_id_counter += 1
            items.append(_random_item(issue_id_counter, day))
        reports.append(DailyReport(date=day, items=items))

    return reports
