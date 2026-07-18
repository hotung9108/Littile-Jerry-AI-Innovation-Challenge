"""
Backend API cho hệ thống Weekly Report Agent + Organizational Brain.

Chạy thử:
    cd backend
    pip install -r requirements.txt
    uvicorn app.main:app --reload --port 8000

Endpoints chính (Weekly Report):
    POST /api/mock/generate           -> sinh dữ liệu mock (mô phỏng Jira) và lưu tạm
    GET  /api/reports/daily           -> xem dữ liệu ngày đang lưu trong bộ nhớ
    POST /api/reports/weekly          -> chạy Agent workflow, trả về báo cáo tuần
    GET  /api/reports/weekly/history  -> lịch sử báo cáo tuần đã lưu (cần DATABASE_URL)
    GET  /health                      -> kiểm tra backend còn sống

Endpoints chính (Organizational Brain) — xem app/knowledge_routes.py:
    POST /api/brain/ingest            -> lấy dữ liệu thô từ Slack/Email/Meeting/GDocs
    POST /api/brain/extract           -> trích xuất tri thức từ dữ liệu vừa ingest
    GET  /api/brain/items             -> xem danh sách tri thức đã trích xuất
    GET  /api/brain/search            -> tìm kiếm bằng ngôn ngữ tự nhiên
    GET  /api/brain/risks             -> phát hiện rủi ro/phụ thuộc
    GET  /api/brain/onboarding        -> tóm tắt onboarding cho người mới
"""
from typing import List, Optional
from datetime import date

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import DailyReport, WeeklyReport
from app.mock_data import generate_mock_daily_reports
from app.agent.workflow import WeeklyReportAgent
from app.knowledge_routes import router as brain_router

app = FastAPI(
    title="Weekly Report Agent + Organizational Brain",
    description=(
        "Agent tự động tổng hợp báo cáo tuần từ Jira (mock hoặc thật), kết hợp "
        "'Organizational Brain' tổng hợp tri thức từ Slack/Email/Meeting/Google Docs."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(brain_router)

# Lưu tạm trong bộ nhớ cho bản demo (luôn hoạt động dù có DB hay không).
_STORE: dict = {"daily_reports": []}

agent = WeeklyReportAgent()


@app.on_event("startup")
def on_startup():
    if settings.DATABASE_URL:
        try:
            from app.db import init_db

            init_db()
            print("[startup] Đã kết nối Postgres và khởi tạo bảng (nếu chưa có).")
        except Exception as e:
            print(f"[startup] Cảnh báo: không thể khởi tạo DB ({e}). Hệ thống vẫn chạy với bộ nhớ tạm.")
    else:
        print("[startup] Chưa cấu hình DATABASE_URL -> dùng bộ nhớ tạm, không lưu lịch sử lâu dài.")

    if settings.ENABLE_SCHEDULER:
        from app.scheduler import start_scheduler

        start_scheduler()


@app.on_event("shutdown")
def on_shutdown():
    if settings.ENABLE_SCHEDULER:
        from app.scheduler import stop_scheduler

        stop_scheduler()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "data_source": settings.DATA_SOURCE,
        "database": "postgres" if settings.DATABASE_URL else "in-memory",
        "llm_provider": settings.LLM_PROVIDER,
    }


@app.post("/api/mock/generate", response_model=List[DailyReport])
def generate_mock(days: int = Query(default=5, ge=1, le=14), items_per_day: int = Query(default=6, ge=1, le=30)):
    """Sinh dữ liệu mock mô phỏng báo cáo hằng ngày lấy từ Jira, lưu vào bộ nhớ."""
    reports = generate_mock_daily_reports(days=days, items_per_day=items_per_day)
    _STORE["daily_reports"] = reports
    return reports


@app.get("/api/reports/daily", response_model=List[DailyReport])
def get_daily_reports():
    """Trả về dữ liệu ngày hiện đang lưu trong bộ nhớ (mock đã sinh gần nhất)."""
    return _STORE["daily_reports"]


@app.post("/api/reports/weekly", response_model=WeeklyReport)
def generate_weekly_report(
    source: str = Query(default="mock", pattern="^(mock|jira)$"),
    days: int = Query(default=5, ge=1, le=14),
    assignee: Optional[str] = Query(default=None, description="Lọc báo cáo theo 1 thành viên"),
    project: Optional[str] = Query(default=None, description="Lọc báo cáo theo 1 dự án"),
):
    """
    Chạy toàn bộ Agent workflow: fetch -> normalize -> (lọc) -> analyze -> summarize.
    Nếu đã cấu hình DATABASE_URL, báo cáo cũng được lưu lại để xem lịch sử sau này.

    source=mock  -> dùng dữ liệu giả (mặc định, không cần cấu hình gì thêm)
    source=jira  -> gọi Jira API thật (cần cấu hình JIRA_URL / JIRA_EMAIL / JIRA_API_TOKEN)
    """
    try:
        report = agent.run(source=source, days=days, assignee=assignee, project=project)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi tạo báo cáo tuần: {e}")

    if settings.DATABASE_URL:
        try:
            _save_weekly_report_to_db(report)
        except Exception as e:
            print(f"[main] Cảnh báo: không lưu được báo cáo vào DB ({e})")

    return report


@app.get("/api/reports/weekly/history", response_model=List[WeeklyReport])
def get_weekly_report_history(limit: int = Query(default=20, ge=1, le=100)):
    """Lấy lịch sử các báo cáo tuần đã lưu (yêu cầu đã cấu hình DATABASE_URL)."""
    if not settings.DATABASE_URL:
        raise HTTPException(
            status_code=400,
            detail="Chưa cấu hình DATABASE_URL trong .env nên không có lịch sử báo cáo để xem.",
        )

    from app.db import get_session_factory
    from app.db_models import WeeklyReportRecord

    SessionLocal = get_session_factory()
    with SessionLocal() as db:
        records = (
            db.query(WeeklyReportRecord)
            .order_by(WeeklyReportRecord.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            WeeklyReport(
                id=r.id,
                week_start=r.week_start,
                week_end=r.week_end,
                source=r.source,
                assignee_filter=r.assignee_filter,
                project_filter=r.project_filter,
                highlights=r.highlights or [],
                completed=r.completed or [],
                in_progress=r.in_progress or [],
                blockers=r.blockers or [],
                decisions=r.decisions or [],
                next_steps=r.next_steps or [],
                raw_stats=r.raw_stats or {},
            )
            for r in records
        ]


def _save_weekly_report_to_db(report: WeeklyReport):
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
        db.refresh(record)
        report.id = record.id
