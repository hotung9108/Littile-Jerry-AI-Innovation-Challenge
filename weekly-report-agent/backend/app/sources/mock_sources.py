"""
Sinh dữ liệu MOCK mô phỏng các kênh làm việc của một tổ chức phi lợi nhuận (NPO):
Slack, Email, Meeting (biên bản họp), Google Docs.

Mỗi nguồn trả về List[RawEvent] — cùng schema với nguồn thật (xem real_sources.py),
nên phần extractor/search/risk_monitor không cần biết dữ liệu đến từ đâu.
"""
import random
from datetime import datetime, timedelta
from typing import List

from app.knowledge_models import RawEvent

TEAMS = ["Gây quỹ", "Chương trình", "Tình nguyện viên", "Truyền thông", "Vận hành"]
PROJECTS = [
    "Chiến dịch gây quỹ Mùa Đông",
    "Dự án hỗ trợ trẻ em vùng cao",
    "Chương trình đào tạo tình nguyện viên mới",
    "Chiến dịch truyền thông Ngày Trẻ Em",
]
PEOPLE = ["Chị Hương", "Anh Nam", "Chị Linh", "Anh Đức", "Chị Mai", "Anh Tuấn"]

SLACK_CHANNELS = ["#gay-quy", "#chuong-trinh", "#tinh-nguyen-vien", "#truyen-thong", "#general"]

SLACK_MESSAGES = [
    ("decision", "Team thống nhất chọn nền tảng Payoo để nhận quyên góp online thay vì chuyển khoản thủ công."),
    ("blocker", "Chưa nhận được xác nhận ngân sách từ ban giám đốc nên chưa thể ký hợp đồng với nhà cung cấp in ấn."),
    ("action_item", "Anh Nam sẽ soạn xong bản đề xuất tài trợ gửi doanh nghiệp trước thứ Sáu tuần này."),
    ("fact", "Số lượng tình nguyện viên đăng ký cho chương trình mùa đông đã vượt 150 người."),
    ("blocker", "Kho vật phẩm quyên góp đang quá tải, cần tìm thêm địa điểm lưu trữ tạm."),
    ("decision", "Quyết định dời ngày tổ chức sự kiện gây quỹ sang tuần sau do trùng lịch với đối tác."),
    ("action_item", "Chị Linh phụ trách liên hệ trường học để sắp xếp lịch trao quà cho trẻ em vùng cao."),
    ("fact", "Chiến dịch truyền thông trên mạng xã hội đạt 20,000 lượt tiếp cận trong tuần qua."),
]

EMAIL_SUBJECTS = [
    ("decision", "Xác nhận: Ngân sách Q3 đã được phê duyệt cho chương trình vùng cao"),
    ("blocker", "Vấn đề: Đối tác vận chuyển chưa phản hồi lịch giao hàng cứu trợ"),
    ("action_item", "Đề nghị: Chuẩn bị báo cáo tài chính quý gửi nhà tài trợ trước ngày 25"),
    ("fact", "Thông báo: Đã nhận được khoản tài trợ 50 triệu từ doanh nghiệp đối tác"),
]

MEETING_TITLES = [
    "Họp giao ban tuần - Team Chương trình",
    "Họp rà soát tiến độ chiến dịch gây quỹ",
    "Họp với nhà tài trợ chiến lược",
    "Họp onboarding tình nguyện viên mới",
]

MEETING_NOTES = [
    ("decision", "Cả team đồng ý dùng mẫu báo cáo mới cho các nhà tài trợ, áp dụng từ quý sau."),
    ("action_item", "Chị Mai chịu trách nhiệm tổng hợp danh sách tình nguyện viên đã hoàn thành đào tạo."),
    ("blocker", "Thiếu nhân sự điều phối tại điểm phát quà, cần tuyển thêm 2 tình nguyện viên trước cuối tháng."),
    ("relationship", "Chiến dịch truyền thông Ngày Trẻ Em phụ thuộc vào việc hoàn tất thiết kế ấn phẩm từ team Truyền thông."),
]

GDOCS_TITLES = [
    "Kế hoạch triển khai Chiến dịch gây quỹ Mùa Đông",
    "Báo cáo tổng kết Dự án hỗ trợ trẻ em vùng cao Q2",
    "Quy trình onboarding tình nguyện viên mới",
    "Biên bản họp ban điều hành tháng này",
]

GDOCS_SNIPPETS = [
    ("decision", "Ban điều hành quyết định mở rộng chương trình sang thêm 2 tỉnh trong năm nay."),
    ("fact", "Tổng số tiền quyên góp lũy kế từ đầu năm đạt 1.2 tỷ đồng."),
    ("action_item", "Cần hoàn thiện tài liệu hướng dẫn onboarding trước khi đợt tình nguyện viên mới bắt đầu."),
    ("blocker", "Ngân sách dành cho vận chuyển vật tư đang vượt dự trù ban đầu 15%."),
]


def _rand_time(day: datetime) -> datetime:
    return day.replace(
        hour=random.randint(8, 18), minute=random.randint(0, 59), second=0, microsecond=0
    )


def generate_mock_slack_events(days: int = 7, per_day: int = 4) -> List[RawEvent]:
    events = []
    today = datetime.utcnow()
    counter = 1000
    for offset in range(days - 1, -1, -1):
        day = today - timedelta(days=offset)
        for _ in range(per_day):
            counter += 1
            kind, text = random.choice(SLACK_MESSAGES)
            events.append(
                RawEvent(
                    source="slack",
                    source_ref=f"slack-msg-{counter}",
                    channel_or_doc=random.choice(SLACK_CHANNELS),
                    author=random.choice(PEOPLE),
                    team=random.choice(TEAMS),
                    project=random.choice(PROJECTS),
                    timestamp=_rand_time(day),
                    content=text,
                )
            )
    return events


def generate_mock_email_events(days: int = 7, per_day: int = 1) -> List[RawEvent]:
    events = []
    today = datetime.utcnow()
    counter = 2000
    for offset in range(days - 1, -1, -1):
        day = today - timedelta(days=offset)
        for _ in range(per_day):
            counter += 1
            kind, subject = random.choice(EMAIL_SUBJECTS)
            events.append(
                RawEvent(
                    source="email",
                    source_ref=f"email-{counter}",
                    channel_or_doc=subject,
                    author=random.choice(PEOPLE),
                    team=random.choice(TEAMS),
                    project=random.choice(PROJECTS),
                    timestamp=_rand_time(day),
                    content=f"{subject}. Chi tiết được trao đổi qua email nội bộ giữa các bên liên quan.",
                )
            )
    return events


def generate_mock_meeting_events(days: int = 7, meetings_per_week: int = 3) -> List[RawEvent]:
    events = []
    today = datetime.utcnow()
    counter = 3000
    for _ in range(meetings_per_week):
        counter += 1
        day = today - timedelta(days=random.randint(0, days - 1))
        title = random.choice(MEETING_TITLES)
        # Mỗi cuộc họp sinh ra vài "khoảnh khắc" tri thức trong biên bản
        for _k in range(random.randint(2, 4)):
            counter += 1
            kind, note = random.choice(MEETING_NOTES)
            events.append(
                RawEvent(
                    source="meeting",
                    source_ref=f"meeting-{counter}",
                    channel_or_doc=title,
                    author=random.choice(PEOPLE),
                    team=random.choice(TEAMS),
                    project=random.choice(PROJECTS),
                    timestamp=_rand_time(day),
                    content=note,
                )
            )
    return events


def generate_mock_gdocs_events(days: int = 7, docs_updated: int = 3) -> List[RawEvent]:
    events = []
    today = datetime.utcnow()
    counter = 4000
    for _ in range(docs_updated):
        counter += 1
        day = today - timedelta(days=random.randint(0, days - 1))
        title = random.choice(GDOCS_TITLES)
        kind, snippet = random.choice(GDOCS_SNIPPETS)
        events.append(
            RawEvent(
                source="gdocs",
                source_ref=f"gdoc-{counter}",
                channel_or_doc=title,
                author=random.choice(PEOPLE),
                team=random.choice(TEAMS),
                project=random.choice(PROJECTS),
                timestamp=_rand_time(day),
                content=snippet,
            )
        )
    return events


def generate_all_mock_events(days: int = 7) -> List[RawEvent]:
    """Sinh dữ liệu mock cho cả 4 kênh cùng lúc — dùng cho endpoint ingest/mock."""
    events = []
    events += generate_mock_slack_events(days=days)
    events += generate_mock_email_events(days=days)
    events += generate_mock_meeting_events(days=days)
    events += generate_mock_gdocs_events(days=days)
    events.sort(key=lambda e: e.timestamp)
    return events
