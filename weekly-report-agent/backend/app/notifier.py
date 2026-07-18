"""
Gửi báo cáo tuần / cảnh báo rủi ro qua Slack (Incoming Webhook) hoặc Email (SMTP).

Cấu hình trong .env:
  SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/yyy/zzz
  SMTP_HOST=smtp.gmail.com
  SMTP_PORT=587
  SMTP_USER=your-email@gmail.com
  SMTP_PASSWORD=app-password
  REPORT_EMAIL_RECIPIENTS=a@org.com,b@org.com

Nếu thiếu cấu hình, hàm tương ứng sẽ bỏ qua và log cảnh báo thay vì lỗi,
để không làm gãy luồng cron job.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

import requests

from app.config import settings
from app.models import WeeklyReport


def _weekly_report_to_text(report: WeeklyReport) -> str:
    def section(title: str, items: list) -> str:
        body = "\n".join(f"  • {b}" for b in items) if items else "  (không có)"
        return f"*{title}*\n{body}\n"

    return (
        f"📊 *Báo cáo tuần {report.week_start} → {report.week_end}* (nguồn: {report.source})\n\n"
        + section("1. Kết quả nổi bật", report.highlights)
        + section("2. Công việc đã hoàn thành", report.completed)
        + section("3. Công việc đang thực hiện", report.in_progress)
        + section("4. Khó khăn", report.blockers)
        + section("5. Quyết định", report.decisions)
        + section("6. Công việc tiếp theo", report.next_steps)
    )


def send_slack_message(text: str) -> bool:
    if not settings.SLACK_WEBHOOK_URL:
        print("[notifier] Bỏ qua gửi Slack: chưa cấu hình SLACK_WEBHOOK_URL")
        return False
    try:
        resp = requests.post(settings.SLACK_WEBHOOK_URL, json={"text": text}, timeout=15)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"[notifier] Gửi Slack thất bại: {e}")
        return False


def send_email(subject: str, body: str, recipients: Optional[list] = None) -> bool:
    recipients = recipients or [
        r.strip() for r in settings.REPORT_EMAIL_RECIPIENTS.split(",") if r.strip()
    ]
    if not (settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD and recipients):
        print("[notifier] Bỏ qua gửi Email: thiếu cấu hình SMTP_* hoặc REPORT_EMAIL_RECIPIENTS")
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_USER
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USER, recipients, msg.as_string())
        return True
    except Exception as e:
        print(f"[notifier] Gửi Email thất bại: {e}")
        return False


def notify_weekly_report(report: WeeklyReport):
    text = _weekly_report_to_text(report)
    send_slack_message(text)
    send_email(
        subject=f"Báo cáo tuần {report.week_start} → {report.week_end}",
        body=text.replace("*", ""),
    )


def notify_risk_alerts(alerts: list):
    if not alerts:
        return
    lines = ["🚨 *Cảnh báo rủi ro tuần này*\n"]
    for a in alerts:
        icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(a.level, "🔵")
        lines.append(f"{icon} *{a.title}*\n  {a.description}\n  → {a.suggested_action}\n")
    text = "\n".join(lines)
    send_slack_message(text)
    send_email(subject="Cảnh báo rủi ro & phụ thuộc", body=text.replace("*", ""))
