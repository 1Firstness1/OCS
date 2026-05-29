import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog

async def log_action(
    db: AsyncSession,
    user_id: uuid.UUID,
    organization_id: uuid.UUID | None,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    details: str | None = None
):
    log = AuditLog(
        user_id=user_id,
        organization_id=organization_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details
    )
    db.add(log)
    # We do not commit here to allow callers to group the log within their transaction
