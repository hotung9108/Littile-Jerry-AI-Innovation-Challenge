"""
Cron job tự động:
  - Cuối mỗi tuần (mặc định: Thứ Sáu 17:00) -> tạo báo cáo tuần + gửi Slack/Email
  - Định kỳ mỗi ngày (mặc định: 9:00 sáng) -> quét rủi ro/phụ thuộc, cảnh báo sớm

Cấu hình lịch trong .env (dùng cron expression chuẩn 5 trường: phút giờ ngày tháng thứ):
  WEEKLY_REPORT_CRON="0 17 * * FRI"
  RISK_CHECK_CRON="0 9 * * *"

Bật/tắt scheduler bằng ENABLE_SCHEDULER=true|false — mặc định false để
không tự động chạy nền khi mới cài đặt/test.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.agent.workflow import WeeklyReportAgent
from app.notifier import notify_weekly_report, notify_risk_alerts
from app.brain.risk_monitor import detect_risks

_scheduler: BackgroundScheduler = None


def _job_generate_and_notify_weekly_report():
    print("[scheduler] Đang tạo báo cáo tuần tự động...")
    try:
        agent = WeeklyReportAgent()
        report = agent.run(source=settings.DATA_SOURCE, days=5)

        if settings.DATABASE_URL:
            from app.knowledge_store import _db_available  # reuse check
            from app.db import get_session_factory
            from app.db_models import WeeklyReportRecord

            SessionLocal = get_session_factory()
            with SessionLocal() as db:
                record = WeeklyReportRecord(
                    week_start=report.week_start,
                    week_end=report.week_end,
                    source=report.source,
                    assignee_filter=report.assignee_filter,
                    project_filter=report.project_filter,
                    highlights=report.highlights,
                    completed=report.completed,
                    in_progress=report.in_progress,
                    blockers=report.blockers,
                    decisions=report.decisions,
                    next_steps=report.next_steps,
                    raw_stats=report.raw_stats,
                )
                db.add(record)
                db.commit()

        notify_weekly_report(report)
        print("[scheduler] Đã tạo và gửi báo cáo tuần thành công.")
    except Exception as e:
        print(f"[scheduler] Lỗi khi tạo báo cáo tuần tự động: {e}")


def _job_check_risks():
    print("[scheduler] Đang quét rủi ro/phụ thuộc...")
    try:
        alerts = detect_risks()
        notify_risk_alerts(alerts)
        print(f"[scheduler] Quét xong, phát hiện {len(alerts)} cảnh báo.")
    except Exception as e:
        print(f"[scheduler] Lỗi khi quét rủi ro: {e}")


def start_scheduler():
    global _scheduler
    if not settings.ENABLE_SCHEDULER:
        print("[scheduler] ENABLE_SCHEDULER=false, không khởi động cron job.")
        return

    _scheduler = BackgroundScheduler(timezone="Asia/Ho_Chi_Minh")
    _scheduler.add_job(
        _job_generate_and_notify_weekly_report,
        CronTrigger.from_crontab(settings.WEEKLY_REPORT_CRON),
        id="weekly_report",
        replace_existing=True,
    )
    _scheduler.add_job(
        _job_check_risks,
        CronTrigger.from_crontab(settings.RISK_CHECK_CRON),
        id="risk_check",
        replace_existing=True,
    )
    _scheduler.start()
    print(
        f"[scheduler] Đã khởi động. Báo cáo tuần: '{settings.WEEKLY_REPORT_CRON}', "
        f"Quét rủi ro: '{settings.RISK_CHECK_CRON}'"
    )


def stop_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
