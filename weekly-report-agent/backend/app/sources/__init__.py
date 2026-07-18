"""
Điểm vào thống nhất để lấy RawEvent từ bất kỳ nguồn nào (mock hoặc thật),
để knowledge_routes.py không cần biết chi tiết từng adapter.
"""
from typing import List

from app.knowledge_models import RawEvent, SourceType
from app.sources import mock_sources
from app.sources.real_sources import SlackSource, EmailSource, MeetingSource, GDocsSource

_REAL_SOURCES = {
    "slack": SlackSource,
    "email": EmailSource,
    "meeting": MeetingSource,
    "gdocs": GDocsSource,
}


def fetch_events(source: SourceType, mode: str = "mock", days: int = 7) -> List[RawEvent]:
    if mode == "mock":
        generator = {
            "slack": mock_sources.generate_mock_slack_events,
            "email": mock_sources.generate_mock_email_events,
            "meeting": mock_sources.generate_mock_meeting_events,
            "gdocs": mock_sources.generate_mock_gdocs_events,
        }[source]
        return generator(days=days)

    if mode == "real":
        adapter_cls = _REAL_SOURCES[source]
        return adapter_cls().fetch_events(days=days)

    raise ValueError(f"mode không hợp lệ: {mode} (chỉ nhận 'mock' hoặc 'real')")
