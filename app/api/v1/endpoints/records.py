from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from decimal import Decimal
from datetime import date

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.user import User
from app.models.financial_record import RecordType, RecordCategory
from app.schemas.financial_record import (
    RecordCreate, RecordUpdate, RecordOut, RecordFilter, PaginatedRecords
)
from app.services.record_service import (
    create_record, get_records, get_record_by_id, update_record, soft_delete_record
)

router = APIRouter(prefix="/records", tags=["Financial Records"])


@router.post("", response_model=RecordOut, status_code=status.HTTP_201_CREATED)
async def create_financial_record(
    data: RecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "analyst")),
):
    """Create a financial record. Analyst and Admin only."""
    return await create_record(db, data, current_user)


@router.get("", response_model=PaginatedRecords)
async def list_records(
    type: Optional[RecordType] = Query(None),
    category: Optional[RecordCategory] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    min_amount: Optional[Decimal] = Query(None),
    max_amount: Optional[Decimal] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),  # All roles can read
):
    """
    List financial records with filtering and pagination.
    All authenticated users (viewer, analyst, admin) can access.
    """
    filters = RecordFilter(
        type=type,
        category=category,
        date_from=date_from,
        date_to=date_to,
        min_amount=min_amount,
        max_amount=max_amount,
        page=page,
        page_size=page_size,
    )
    return await get_records(db, filters)


@router.get("/{record_id}", response_model=RecordOut)
async def get_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single record. All authenticated users can access."""
    return await get_record_by_id(db, record_id)


@router.patch("/{record_id}", response_model=RecordOut)
async def update_financial_record(
    record_id: int,
    data: RecordUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """Update a record. Admin only."""
    return await update_record(db, record_id, data, current_user)


@router.delete("/{record_id}", status_code=status.HTTP_200_OK)
async def delete_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    """
    Soft-delete a record. Admin only.
    Records are NEVER hard-deleted — they are archived with a timestamp and actor ID.
    """
    return await soft_delete_record(db, record_id, current_user)
