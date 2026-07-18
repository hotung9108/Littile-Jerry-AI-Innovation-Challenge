import json
import smtplib
from email.message import EmailMessage
from typing import Optional

import requests

from app.config import settings
from app.models import WeeklyReport


def format_weekly_report_text(report: WeeklyReport) -> str:
    lines = [
        f"Báo cáo tuần: {report.week_start} -> {report.week_end}",
        f"Nguồn: {report.source}",
        "",
    ]
    if report.highlights:
        lines.append("Kết quả nổi bật:")
        lines.extend([f"- {item}" for item in report.highlights])
        lines.append("")
    if report.completed:
        lines.append("Công việc đã hoàn thành:")
        lines.extend([f"- {item}" for item in report.completed])
        lines.append("")
    if report.in_progress:
        lines.append("Công việc đang thực hiện:")
        lines.extend([f"- {item}" for item in report.in_progress])
        lines.append("")
    if report.blockers:
        lines.append("Khó khăn / vướng mắc:")
        lines.extend([f"- {item}" for item in report.blockers])
        lines.append("")
    if report.decisions:
        lines.append("Quyết định:")
        lines.extend([f"- {item}" for item in report.decisions])
        lines.append("")
    if report.next_steps:
        lines.append("Công việc tiếp theo:")
        lines.extend([f"- {item}" for item in report.next_steps])
        lines.append("")
    lines.append("Raw stats:")
    lines.append(json.dumps(report.raw_stats, ensure_ascii=False, indent=2))
    return "\n".join(lines)


def send_slack_message(text: str) -> None:
    webhook = settings.SLACK_WEBHOOK_URL
    if not webhook:
        return

    payload = {"text": text}
    if settings.SLACK_CHANNEL:
        payload["channel"] = settings.SLACK_CHANNEL

    resp = requests.post(webhook, json=payload, timeout=10)
    resp.raise_for_status()


def send_email(subject: str, body: str, recipients: Optional[str] = None) -> None:
    if not settings.EMAIL_SMTP_HOST or not settings.EMAIL_TO:
        return

    recipients_list = [addr.strip() for addr in (recipients or settings.EMAIL_TO).split(",") if addr.strip()]
    if not recipients_list:
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = ", ".join(recipients_list)
    msg.set_content(body)

    port = int(settings.EMAIL_SMTP_PORT or 587)
    with smtplib.SMTP(settings.EMAIL_SMTP_HOST, port, timeout=20) as smtp:
        if settings.EMAIL_USE_TLS:
            smtp.starttls()
        if settings.EMAIL_USERNAME and settings.EMAIL_PASSWORD:
            smtp.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
        smtp.send_message(msg)


def dispatch_weekly_report(report: WeeklyReport) -> None:
    text = format_weekly_report_text(report)
    if settings.SLACK_WEBHOOK_URL:
        send_slack_message(text)
    if settings.EMAIL_SMTP_HOST and settings.EMAIL_TO:
        subject = f"Báo cáo tuần {report.week_start} - {report.week_end}"
        send_email(subject, text)
