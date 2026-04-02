import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.database import engine, Base, AsyncSessionLocal
from app.api.v1 import router as api_router
from app.core.config import settings

logger = logging.getLogger(__name__)


async def run_migrations():
    """Run alembic migrations programmatically on startup."""
    import asyncio
    from alembic.config import Config
    from alembic import command

    def _run():
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")

    # Run in thread pool — alembic is sync
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _run)
    logger.info("Migrations applied successfully")


async def run_seed():
    """Seed admin/analyst/viewer users if no users exist yet."""
    from sqlalchemy import select, func
    from app.models.user import User, UserRole
    from app.models.financial_record import FinancialRecord, RecordType, RecordCategory
    from app.core.security import hash_password
    from decimal import Decimal
    from datetime import date

    async with AsyncSessionLocal() as db:
        # Check if already seeded
        result = await db.execute(select(func.count()).select_from(User))
        count = result.scalar_one()
        if count > 0:
            logger.info(f"Seed skipped — {count} users already exist")
            return

        logger.info("Seeding initial users and sample records...")

        # Create users
        admin = User(email="admin@finvault.io", full_name="Admin User",
                     hashed_password=hash_password("Admin@1234"), role=UserRole.ADMIN)
        analyst = User(email="analyst@finvault.io", full_name="Analyst User",
                       hashed_password=hash_password("Analyst@1234"), role=UserRole.ANALYST)
        viewer = User(email="viewer@finvault.io", full_name="Viewer User",
                      hashed_password=hash_password("Viewer@1234"), role=UserRole.VIEWER)
        db.add_all([admin, analyst, viewer])
        await db.flush()

        # Sample financial records
        records = [
            FinancialRecord(amount=Decimal("500000.00"), type=RecordType.INCOME,
                category=RecordCategory.REVENUE, record_date=date(2026, 1, 15),
                description="Q1 SaaS revenue", created_by=admin.id),
            FinancialRecord(amount=Decimal("120000.00"), type=RecordType.INCOME,
                category=RecordCategory.INVESTMENT, record_date=date(2026, 1, 20),
                description="Seed round tranche", created_by=admin.id),
            FinancialRecord(amount=Decimal("85000.00"), type=RecordType.EXPENSE,
                category=RecordCategory.PAYROLL, record_date=date(2026, 1, 31),
                description="January payroll", created_by=admin.id),
            FinancialRecord(amount=Decimal("22000.00"), type=RecordType.EXPENSE,
                category=RecordCategory.INFRASTRUCTURE, record_date=date(2026, 2, 5),
                description="AWS + Supabase", created_by=admin.id),
            FinancialRecord(amount=Decimal("15000.00"), type=RecordType.EXPENSE,
                category=RecordCategory.MARKETING, record_date=date(2026, 2, 10),
                description="LinkedIn ads", created_by=admin.id),
            FinancialRecord(amount=Decimal("620000.00"), type=RecordType.INCOME,
                category=RecordCategory.REVENUE, record_date=date(2026, 2, 15),
                description="Q1 revenue top-up", created_by=admin.id),
            FinancialRecord(amount=Decimal("90000.00"), type=RecordType.EXPENSE,
                category=RecordCategory.PAYROLL, record_date=date(2026, 2, 28),
                description="February payroll", created_by=admin.id),
            FinancialRecord(amount=Decimal("12500.00"), type=RecordType.EXPENSE,
                category=RecordCategory.COMPLIANCE, record_date=date(2026, 3, 1),
                description="SOC2 audit fees", created_by=admin.id),
            FinancialRecord(amount=Decimal("750000.00"), type=RecordType.INCOME,
                category=RecordCategory.REVENUE, record_date=date(2026, 3, 15),
                description="Q2 SaaS revenue", created_by=admin.id),
            FinancialRecord(amount=Decimal("35000.00"), type=RecordType.EXPENSE,
                category=RecordCategory.OPERATIONS, record_date=date(2026, 3, 20),
                description="Office + misc ops", created_by=admin.id),
        ]
        db.add_all(records)
        await db.commit()
        logger.info("Seed complete — 3 users + 10 records created")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Run migrations
    await run_migrations()
    # 2. Seed if empty
    await run_seed()
    yield


app = FastAPI(
    title="FinVault API",
    description=(
        "Compliant finance record management backend with role-based access control, "
        "audit logging, and dashboard analytics. Built for Zorvyn assessment."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "FinVault API",
        "version": "1.0.0",
        "status": "healthy",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
