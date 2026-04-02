from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, extract, case

from app.models.financial_record import FinancialRecord, RecordType, RecordCategory
from app.schemas.dashboard import DashboardSummary, CategoryTotal, MonthlyTrend, RecentRecord

MONTH_LABELS = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
    5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
    9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}


async def get_dashboard_summary(db: AsyncSession) -> DashboardSummary:
    base_filter = FinancialRecord.is_deleted == False

    # --- Totals ---
    totals_result = await db.execute(
        select(
            func.coalesce(
                func.sum(case((FinancialRecord.type == RecordType.INCOME, FinancialRecord.amount), else_=0)),
                Decimal("0"),
            ).label("total_income"),
            func.coalesce(
                func.sum(case((FinancialRecord.type == RecordType.EXPENSE, FinancialRecord.amount), else_=0)),
                Decimal("0"),
            ).label("total_expense"),
            func.count(FinancialRecord.id).label("record_count"),
        ).where(base_filter)
    )
    totals = totals_result.one()
    total_income = totals.total_income or Decimal("0")
    total_expense = totals.total_expense or Decimal("0")

    # --- Category breakdown: Income ---
    income_cat_result = await db.execute(
        select(
            FinancialRecord.category,
            func.sum(FinancialRecord.amount).label("total"),
            func.count(FinancialRecord.id).label("count"),
        )
        .where(and_(base_filter, FinancialRecord.type == RecordType.INCOME))
        .group_by(FinancialRecord.category)
        .order_by(func.sum(FinancialRecord.amount).desc())
    )
    income_by_category = [
        CategoryTotal(category=row.category, total=row.total, count=row.count)
        for row in income_cat_result.all()
    ]

    # --- Category breakdown: Expense ---
    expense_cat_result = await db.execute(
        select(
            FinancialRecord.category,
            func.sum(FinancialRecord.amount).label("total"),
            func.count(FinancialRecord.id).label("count"),
        )
        .where(and_(base_filter, FinancialRecord.type == RecordType.EXPENSE))
        .group_by(FinancialRecord.category)
        .order_by(func.sum(FinancialRecord.amount).desc())
    )
    expense_by_category = [
        CategoryTotal(category=row.category, total=row.total, count=row.count)
        for row in expense_cat_result.all()
    ]

    # --- Monthly trends (last 12 months) ---
    monthly_result = await db.execute(
        select(
            extract("year", FinancialRecord.record_date).label("year"),
            extract("month", FinancialRecord.record_date).label("month"),
            func.coalesce(
                func.sum(case((FinancialRecord.type == RecordType.INCOME, FinancialRecord.amount), else_=0)),
                Decimal("0"),
            ).label("income"),
            func.coalesce(
                func.sum(case((FinancialRecord.type == RecordType.EXPENSE, FinancialRecord.amount), else_=0)),
                Decimal("0"),
            ).label("expense"),
        )
        .where(base_filter)
        .group_by("year", "month")
        .order_by("year", "month")
        .limit(12)
    )
    monthly_trends = [
        MonthlyTrend(
            year=int(row.year),
            month=int(row.month),
            month_label=MONTH_LABELS[int(row.month)],
            income=row.income or Decimal("0"),
            expense=row.expense or Decimal("0"),
            net=(row.income or Decimal("0")) - (row.expense or Decimal("0")),
        )
        for row in monthly_result.all()
    ]

    # --- Recent activity (last 10 records) ---
    recent_result = await db.execute(
        select(FinancialRecord)
        .where(base_filter)
        .order_by(FinancialRecord.created_at.desc())
        .limit(10)
    )
    recent_records = [
        RecentRecord(
            id=r.id,
            amount=r.amount,
            type=r.type,
            category=r.category,
            description=r.description,
            record_date=str(r.record_date),
        )
        for r in recent_result.scalars().all()
    ]

    return DashboardSummary(
        total_income=total_income,
        total_expense=total_expense,
        net_balance=total_income - total_expense,
        record_count=totals.record_count,
        income_by_category=income_by_category,
        expense_by_category=expense_by_category,
        monthly_trends=monthly_trends,
        recent_activity=recent_records,
    )
