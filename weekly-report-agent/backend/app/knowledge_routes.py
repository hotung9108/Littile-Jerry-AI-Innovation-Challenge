"""
API endpoints cho "Organizational Brain":
  - Ingest dữ liệu (mock hoặc thật) từ Slack/Email/Meeting/GDocs
  - Trích xuất tri thức (KnowledgeItem) từ dữ liệu đã ingest
  - Xem/lọc danh sách KnowledgeItem
  - Tìm kiếm bằng ngôn ngữ tự nhiên (Institutional Memory search)
  - Phát hiện rủi ro/phụ thuộc (risk & dependency monitor)
  - Tạo bản tóm tắt onboarding cho tình nguyện viên/nhân sự mới
"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.knowledge_models import RawEvent, KnowledgeItem, SearchResult, RiskAlert, OnboardingBrief
from app.sources import fetch_events
from app.brain.extractor import extract_knowledge
from app.brain.search import search_knowledge
from app.brain.risk_monitor import detect_risks
from app.brain.onboarding import generate_onboarding_brief
from app import knowledge_store

router = APIRouter(prefix="/api/brain", tags=["organizational-brain"])

# Lưu tạm RawEvent vừa ingest (trước khi extract), để có thể xem lại/debug
_RAW_EVENTS_STORE: List[RawEvent] = []


@router.post("/ingest", response_model=List[RawEvent])
def ingest_events(
    source: str = Query(..., pattern="^(slack|email|meeting|gdocs|all)$"),
    mode: str = Query(default="mock", pattern="^(mock|real)$"),
    days: int = Query(default=7, ge=1, le=30),
):
    """
    Lấy dữ liệu thô (RawEvent) từ 1 nguồn cụ thể, hoặc 'all' để lấy cả 4 nguồn cùng lúc.
    mode=mock  -> dữ liệu giả lập, dùng để test/demo ngay không cần cấu hình gì.
    mode=real  -> gọi API thật (Slack/Email/Meeting/GDocs), cần cấu hình trong .env.
    """
    global _RAW_EVENTS_STORE
    try:
        if source == "all":
            if mode == "mock":
                from app.sources.mock_sources import generate_all_mock_events
                events = generate_all_mock_events(days=days)
            else:
                events = []
                for s in ("slack", "email", "meeting", "gdocs"):
                    try:
                        events += fetch_events(s, mode=mode, days=days)
                    except Exception as e:
                        print(f"[ingest] Bỏ qua nguồn {s} do lỗi: {e}")
        else:
            events = fetch_events(source, mode=mode, days=days)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy dữ liệu: {e}")

    _RAW_EVENTS_STORE = events
    return events


@router.post("/extract", response_model=List[KnowledgeItem])
def extract_and_store():
    """
    Chạy Extraction Agent trên dữ liệu vừa ingest (/api/brain/ingest),
    lưu kết quả vào knowledge store (bộ nhớ tạm hoặc Postgres nếu đã cấu hình).
    """
    if not _RAW_EVENTS_STORE:
        raise HTTPException(
            status_code=400,
            detail="Chưa có dữ liệu để trích xuất. Gọi /api/brain/ingest trước.",
        )
    items = extract_knowledge(_RAW_EVENTS_STORE)
    saved = knowledge_store.save_items(items)
    return saved


@router.get("/items", response_model=List[KnowledgeItem])
def list_knowledge_items(
    project: Optional[str] = None,
    team: Optional[str] = None,
    type: Optional[str] = Query(default=None, pattern="^(decision|action_item|blocker|relationship|fact)$"),
    status: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
):
    """Xem danh sách tri thức đã trích xuất, có thể lọc theo dự án/team/loại/trạng thái."""
    return knowledge_store.list_items(
        project=project, team=team, type_=type, status=status, limit=limit
    )


@router.get("/search", response_model=SearchResult)
def search(
    q: str = Query(..., min_length=2, description="Câu hỏi bằng ngôn ngữ tự nhiên"),
    project: Optional[str] = None,
    team: Optional[str] = None,
):
    """
    Tìm kiếm / truy vấn Institutional Memory bằng ngôn ngữ tự nhiên.
    Ví dụ: "Tuần trước team gây quỹ gặp khó khăn gì?"
    """
    return search_knowledge(q, project=project, team=team)


@router.get("/risks", response_model=List[RiskAlert])
def get_risks(project: Optional[str] = None, team: Optional[str] = None):
    """Quét và trả về danh sách rủi ro/phụ thuộc đang cần chú ý."""
    return detect_risks(project=project, team=team)


@router.get("/onboarding", response_model=OnboardingBrief)
def onboarding_brief(project: Optional[str] = None):
    """Tạo bản tóm tắt kiến thức nền cho người mới tham gia dự án."""
    return generate_onboarding_brief(project=project)


@router.post("/reset")
def reset_demo_data():
    """Chỉ dùng cho demo: xoá sạch dữ liệu mock đang lưu tạm trong bộ nhớ."""
    global _RAW_EVENTS_STORE
    _RAW_EVENTS_STORE = []
    knowledge_store.clear_memory_store()
    return {"status": "cleared"}
