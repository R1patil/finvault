from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, field_validator

from app.models.financial_record import RecordType, RecordCategory


class RecordCreate(BaseModel):
    amount: Decimal
    type: RecordType
    category: RecordCategory
    description: Optional[str] = None
    record_date: date
    reference_number: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v


class RecordUpdate(BaseModel):
    amount: Optional[Decimal] = None
    type: Optional[RecordType] = None
    category: Optional[RecordCategory] = None
    description: Optional[str] = None
    record_date: Optional[date] = None
    reference_number: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v


class RecordOut(BaseModel):
    id: int
    amount: Decimal
    type: RecordType
    category: RecordCategory
    description: Optional[str]
    record_date: date
    reference_number: Optional[str]
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RecordFilter(BaseModel):
    type: Optional[RecordType] = None
    category: Optional[RecordCategory] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    page: int = 1
    page_size: int = 20

    @field_validator("page")
    @classmethod
    def page_positive(cls, v):
        if v < 1:
            raise ValueError("Page must be >= 1")
        return v

    @field_validator("page_size")
    @classmethod
    def page_size_valid(cls, v):
        if not (1 <= v <= 100):
            raise ValueError("Page size must be between 1 and 100")
        return v


class PaginatedRecords(BaseModel):
    items: list[RecordOut]
    total: int
    page: int
    page_size: int
    total_pages: int
