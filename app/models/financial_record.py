from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy import String, Numeric, Date, DateTime, Text, ForeignKey, Enum as SAEnum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


class RecordType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"


class RecordCategory(str, enum.Enum):
    SALARY = "salary"
    REVENUE = "revenue"
    INVESTMENT = "investment"
    OPERATIONS = "operations"
    MARKETING = "marketing"
    INFRASTRUCTURE = "infrastructure"
    PAYROLL = "payroll"
    TAX = "tax"
    COMPLIANCE = "compliance"
    OTHER = "other"


class FinancialRecord(Base):
    __tablename__ = "financial_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    type: Mapped[str] = mapped_column(
        SAEnum(RecordType, name="record_type", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        SAEnum(RecordCategory, name="record_category", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(Text, nullable=True)
    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    reference_number: Mapped[str] = mapped_column(String(100), nullable=True, index=True)

    # Soft delete — records are NEVER hard-deleted (compliance requirement)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Audit fields
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    updated_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    created_by_user = relationship("User", back_populates="records", foreign_keys=[created_by])
