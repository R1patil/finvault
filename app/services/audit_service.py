from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def write_audit_log(
    db: AsyncSession,
    actor_id: int,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    payload: Optional[dict] = None,
    ip_address: Optional[str] = None,
):
    """
    Write an immutable audit log entry.
    Called after every state-changing operation.

    Actions: CREATE, UPDATE, DELETE (soft), LOGIN, ROLE_CHANGE, STATUS_CHANGE
    """
    log = AuditLog(
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else None,
        payload=payload,
        ip_address=ip_address,
    )
    db.add(log)
    # No commit here — caller's transaction handles it
