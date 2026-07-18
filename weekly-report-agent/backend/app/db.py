"""
Kết nối database (Postgres) qua SQLAlchemy.

Dùng để lưu lịch sử báo cáo tuần thay vì chỉ giữ trong bộ nhớ tạm.
Nếu DATABASE_URL không được cấu hình, các chỗ gọi tới DB sẽ báo lỗi rõ ràng
thay vì crash ngầm — nhưng phần tạo báo cáo (API /api/reports/weekly) vẫn
hoạt động bình thường dù không có DB (chỉ là không lưu lại lịch sử).
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

Base = declarative_base()

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        if not settings.DATABASE_URL:
            raise RuntimeError(
                "Chưa cấu hình DATABASE_URL trong .env. "
                "Ví dụ: postgresql+psycopg2://user:password@localhost:5432/weekly_report"
            )
        _engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)
    return _SessionLocal


def init_db():
    """Tạo bảng nếu chưa tồn tại. Gọi 1 lần khi backend khởi động."""
    from app import db_models  # noqa: F401  (đảm bảo model được đăng ký với Base)

    Base.metadata.create_all(bind=get_engine())


def get_db():
    """FastAPI dependency: mở session, đảm bảo đóng lại sau khi dùng xong."""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
