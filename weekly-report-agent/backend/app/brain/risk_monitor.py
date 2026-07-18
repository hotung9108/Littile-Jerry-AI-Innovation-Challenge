"""
Risk & Dependency Monitor.

Quét toàn bộ KnowledgeItem để phát hiện SỚM các rủi ro:
  - Blocker tồn tại quá lâu (stale) mà chưa được giải quyết
  - Action item chưa có tiến triển sau một khoảng thời gian
  - Relationship (phụ thuộc) giữa các team/dự án có 1 bên đang bị chặn
    -> rủi ro dây chuyền sang các phần phụ thuộc

Có thể chạy thủ công (GET /api/brain/risks) hoặc định kỳ qua cron
(xem app/scheduler.py) để chủ động cảnh báo qua Slack/Email TRƯỚC khi
vấn đề trở nên nghiêm trọng.
"""
from datetime import datetime, timedelta
from typing import List

from app.knowledge_models import KnowledgeItem, RiskAlert
from app import knowledge_store

STALE_BLOCKER_DAYS = 5
STALE_ACTION_DAYS = 7


def _age_days(item: KnowledgeItem) -> int:
    return (datetime.utcnow() - item.created_at.replace(tzinfo=None)).days


def detect_risks(project: str = None, team: str = None) -> List[RiskAlert]:
    items = knowledge_store.list_items(project=project, team=team, limit=1000)
    alerts: List[RiskAlert] = []

    # 1. Blocker tồn đọng quá lâu
    stale_blockers = [
        i for i in items
        if i.type == "blocker" and i.status == "open" and _age_days(i) >= STALE_BLOCKER_DAYS
    ]
    for i in stale_blockers:
        alerts.append(
            RiskAlert(
                level="critical" if _age_days(i) >= STALE_BLOCKER_DAYS * 2 else "warning",
                title=f"Khó khăn tồn đọng {_age_days(i)} ngày: {i.project or i.team or 'chưa rõ dự án'}",
                description=i.summary,
                related_items=[i],
                suggested_action=(
                    f"Cần {i.owner or 'người phụ trách'} hoặc trưởng nhóm {i.team or ''} "
                    "trực tiếp can thiệp để gỡ vướng, vì đã kéo dài quá lâu."
                ),
            )
        )

    # 2. Action item chưa có tiến triển
    stale_actions = [
        i for i in items
        if i.type == "action_item" and i.status == "open" and _age_days(i) >= STALE_ACTION_DAYS
    ]
    for i in stale_actions:
        alerts.append(
            RiskAlert(
                level="warning",
                title=f"Công việc chưa cập nhật sau {_age_days(i)} ngày",
                description=i.summary,
                related_items=[i],
                suggested_action=f"Nhắc {i.owner or 'người phụ trách'} cập nhật tiến độ hoặc dời deadline.",
            )
        )

    # 3. Phụ thuộc chéo team/dự án đang có blocker liên quan
    relationships = [i for i in items if i.type == "relationship"]
    open_blockers_by_project = {}
    for b in items:
        if b.type == "blocker" and b.status == "open" and b.project:
            open_blockers_by_project.setdefault(b.project, []).append(b)

    for rel in relationships:
        related_blockers = open_blockers_by_project.get(rel.project, [])
        if related_blockers:
            alerts.append(
                RiskAlert(
                    level="warning",
                    title=f"Rủi ro dây chuyền: {rel.project or 'dự án liên quan'}",
                    description=(
                        f"{rel.summary} — nhưng dự án này đang có {len(related_blockers)} "
                        "khó khăn chưa giải quyết, có thể ảnh hưởng tới các công việc phụ thuộc."
                    ),
                    related_items=[rel] + related_blockers,
                    suggested_action="Rà soát lại timeline của các công việc phụ thuộc trước khi cam kết deadline mới.",
                )
            )

    return alerts
