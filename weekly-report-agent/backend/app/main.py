"""
Backend API cho hệ thống Báo cáo tuần tự động.

Chạy thử:
    cd backend
    pip install -r requirements.txt
    uvicorn app.main:app --reload --port 8000

Endpoints chính:
    POST /api/mock/generate       -> sinh dữ liệu mock (mô phỏng Jira) và lưu tạm
    GET  /api/reports/daily       -> xem dữ liệu ngày đang lưu trong bộ nhớ
    POST /api/reports/weekly      -> chạy Agent workflow, trả về báo cáo tuần
    GET  /health                  -> kiểm tra backend còn sống
"""
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import DailyReport, WeeklyReport
from app.mock_data import generate_mock_daily_reports
from app.agent.workflow import WeeklyReportAgent

app = FastAPI(
    title="Weekly Report Agent",
    description="Agent tự động tổng hợp báo cáo tuần từ dữ liệu Jira (mock hoặc thật).",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lưu tạm trong bộ nhớ cho bản demo (không cần database).
# Khi triển khai thật, có thể thay bằng Postgres/Redis...
_STORE: dict = {"daily_reports": []}

agent = WeeklyReportAgent()


@app.get("/health")
def health():
    return {"status": "ok", "data_source": settings.DATA_SOURCE}


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
):
    """
    Chạy toàn bộ Agent workflow: fetch -> normalize -> analyze -> summarize.

    source=mock  -> dùng dữ liệu giả (mặc định, không cần cấu hình gì thêm)
    source=jira  -> gọi Jira API thật (cần cấu hình JIRA_URL / JIRA_EMAIL / JIRA_API_TOKEN)
    """
    try:
        report = agent.run(source=source, days=days)
    except RuntimeError as e:
        # Ví dụ: thiếu cấu hình Jira
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi tạo báo cáo tuần: {e}")

    return report
