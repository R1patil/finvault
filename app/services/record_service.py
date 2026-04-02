from datetime import datetime, timezone
from typing import Optional
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, extract
from fastapi import HTTPException, status

from app.models.financial_record import FinancialRecord, RecordType, RecordCategory
from app.models.user import User
from app.schemas.financial_record import RecordCreate, RecordUpdate, RecordFilter, PaginatedRecords, RecordOut
from app.services.audit_service import write_audit_log


async def create_record(
    db: AsyncSession,
    data: RecordCreate,
    actor: User,
) -> FinancialRecord:
    record = FinancialRecord(
        **data.model_dump(),
        created_by=actor.id,
        updated_by=actor.id,
    )
    db.add(record)
    await db.flush()  # Get ID before audit log

    await write_audit_log(
        db,
        actor_id=actor.id,
        action="CREATE",
        resource_type="financial_record",
        resource_id=record.id,
        payload={"after": data.model_dump(mode="json")},
    )
    return record


async def get_records(
    db: AsyncSession,
    filters: RecordFilter,
) -> PaginatedRecords:
    query = select(FinancialRecord).where(FinancialRecord.is_deleted == False)

    if filters.type:
        query = query.where(FinancialRecord.type == filters.type)
    if filters.category:
        query = query.where(FinancialRecord.category == filters.category)
    if filters.date_from:
        query = query.where(FinancialRecord.record_date >= filters.date_from)
    if filters.date_to:
        query = query.where(FinancialRecord.record_date <= filters.date_to)
    if filters.min_amount:
        query = query.where(FinancialRecord.amount >= filters.min_amount)
    if filters.max_amount:
        query = query.where(FinancialRecord.amount <= filters.max_amount)

    # Count total
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    # Paginate
    offset = (filters.page - 1) * filters.page_size
    query = query.order_by(FinancialRecord.record_date.desc()).offset(offset).limit(filters.page_size)
    result = await db.execute(query)
    records = result.scalars().all()

    return PaginatedRecords(
        items=[RecordOut.model_validate(r) for r in records],
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        total_pages=max(1, -(-total // filters.page_size)),  # Ceiling division
    )


async def get_record_by_id(db: AsyncSession, record_id: int) -> FinancialRecord:
    result = await db.execute(
        select(FinancialRecord).where(
            and_(FinancialRecord.id == record_id, FinancialRecord.is_deleted == False)
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return record


async def update_record(
    db: AsyncSession,
    record_id: int,
    data: RecordUpdate,
    actor: User,
) -> FinancialRecord:
    record = await get_record_by_id(db, record_id)

    before_snapshot = {
        "amount": str(record.amount),
        "type": record.type,
        "category": record.category,
        "description": record.description,
        "record_date": str(record.record_date),
    }

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(record, key, value)
    record.updated_by = actor.id
    record.updated_at = datetime.now(timezone.utc)

    await write_audit_log(
        db,
        actor_id=actor.id,
        action="UPDATE",
        resource_type="financial_record",
        resource_id=record_id,
        payload={"before": before_snapshot, "after": data.model_dump(mode="json", exclude_unset=True)},
    )
    return record


async def soft_delete_record(
    db: AsyncSession,
    record_id: int,
    actor: User,
) -> dict:
    record = await get_record_by_id(db, record_id)

    record.is_deleted = True
    record.deleted_at = datetime.now(timezone.utc)
    record.deleted_by = actor.id

    await write_audit_log(
        db,
        actor_id=actor.id,
        action="DELETE",
        resource_type="financial_record",
        resource_id=record_id,
        payload={"note": "soft_delete", "record_date": str(record.record_date), "amount": str(record.amount)},
    )
    return {"message": f"Record {record_id} has been archived (soft deleted)"}
