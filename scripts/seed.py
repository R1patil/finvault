"""
Seed script — creates an admin user + sample financial records.
Run once after migrations:
    python scripts/seed.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.financial_record import FinancialRecord, RecordType, RecordCategory
from app.models.audit_log import AuditLog
from app.core.database import Base


async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as db:
        # Create users
        admin = User(
            email="admin@finvault.io",
            full_name="Admin User",
            hashed_password=hash_password("Admin@1234"),
            role=UserRole.ADMIN,
        )
        analyst = User(
            email="analyst@finvault.io",
            full_name="Analyst User",
            hashed_password=hash_password("Analyst@1234"),
            role=UserRole.ANALYST,
        )
        viewer = User(
            email="viewer@finvault.io",
            full_name="Viewer User",
            hashed_password=hash_password("Viewer@1234"),
            role=UserRole.VIEWER,
        )
        db.add_all([admin, analyst, viewer])
        await db.flush()

        # Sample records
        records = [
            FinancialRecord(amount=Decimal("500000.00"), type=RecordType.INCOME,  category=RecordCategory.REVENUE,        record_date=date(2026, 1, 15), description="Q1 SaaS revenue",          created_by=admin.id),
            FinancialRecord(amount=Decimal("120000.00"), type=RecordType.INCOME,  category=RecordCategory.INVESTMENT,     record_date=date(2026, 1, 20), description="Seed round tranche",       created_by=admin.id),
            FinancialRecord(amount=Decimal("85000.00"),  type=RecordType.EXPENSE, category=RecordCategory.PAYROLL,        record_date=date(2026, 1, 31), description="January payroll",          created_by=admin.id),
            FinancialRecord(amount=Decimal("22000.00"),  type=RecordType.EXPENSE, category=RecordCategory.INFRASTRUCTURE, record_date=date(2026, 2, 5),  description="AWS + Supabase",           created_by=admin.id),
            FinancialRecord(amount=Decimal("15000.00"),  type=RecordType.EXPENSE, category=RecordCategory.MARKETING,      record_date=date(2026, 2, 10), description="LinkedIn ads",             created_by=admin.id),
            FinancialRecord(amount=Decimal("620000.00"), type=RecordType.INCOME,  category=RecordCategory.REVENUE,        record_date=date(2026, 2, 15), description="Q1 revenue top-up",        created_by=admin.id),
            FinancialRecord(amount=Decimal("90000.00"),  type=RecordType.EXPENSE, category=RecordCategory.PAYROLL,        record_date=date(2026, 2, 28), description="February payroll",         created_by=admin.id),
            FinancialRecord(amount=Decimal("12500.00"),  type=RecordType.EXPENSE, category=RecordCategory.COMPLIANCE,     record_date=date(2026, 3, 1),  description="SOC2 audit fees",          created_by=admin.id),
            FinancialRecord(amount=Decimal("750000.00"), type=RecordType.INCOME,  category=RecordCategory.REVENUE,        record_date=date(2026, 3, 15), description="Q2 SaaS revenue",          created_by=admin.id),
            FinancialRecord(amount=Decimal("35000.00"),  type=RecordType.EXPENSE, category=RecordCategory.OPERATIONS,     record_date=date(2026, 3, 20), description="Office + misc ops",        created_by=admin.id),
        ]
        db.add_all(records)
        await db.commit()

    print("✅ Seed complete!")
    print("   Admin:    admin@finvault.io   / Admin@1234")
    print("   Analyst:  analyst@finvault.io / Analyst@1234")
    print("   Viewer:   viewer@finvault.io  / Viewer@1234")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
