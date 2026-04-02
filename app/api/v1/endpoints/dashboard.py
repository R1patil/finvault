from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.dashboard import DashboardSummary, AuditLogOut
from app.services.dashboard_service import get_dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Analytics"])


@router.get("/summary", response_model=DashboardSummary)
async def dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),  # All roles
):
    """
    Full dashboard summary: totals, category breakdown, monthly trends, recent activity.
    Accessible to all authenticated users (viewer, analyst, admin).
    """
    return await get_dashboard_summary(db)


@router.get("/audit-logs", response_model=list[AuditLogOut])
async def get_audit_logs(
    resource_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    actor_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),  # Admin only
):
    """
    View audit logs. Admin only.
    Supports filtering by resource type, action, and actor.
    """
    query = select(AuditLog)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    if action:
        query = query.where(AuditLog.action == action)
    if actor_id:
        query = query.where(AuditLog.actor_id == actor_id)

    query = query.order_by(AuditLog.timestamp.desc()).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()

    # Fetch actor emails
    from app.models.user import User as UserModel
    actor_ids = list({log.actor_id for log in logs})
    users_result = await db.execute(select(UserModel).where(UserModel.id.in_(actor_ids)))
    user_map = {u.id: u.email for u in users_result.scalars().all()}

    return [
        AuditLogOut(
            id=log.id,
            actor_id=log.actor_id,
            actor_email=user_map.get(log.actor_id),
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            payload=log.payload,
            timestamp=log.timestamp.isoformat(),
        )
        for log in logs
    ]
