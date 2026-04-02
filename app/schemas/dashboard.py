from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class CategoryTotal(BaseModel):
    category: str
    total: Decimal
    count: int


class MonthlyTrend(BaseModel):
    year: int
    month: int
    month_label: str
    income: Decimal
    expense: Decimal
    net: Decimal


class RecentRecord(BaseModel):
    id: int
    amount: Decimal
    type: str
    category: str
    description: Optional[str]
    record_date: str


class DashboardSummary(BaseModel):
    total_income: Decimal
    total_expense: Decimal
    net_balance: Decimal
    record_count: int
    income_by_category: list[CategoryTotal]
    expense_by_category: list[CategoryTotal]
    monthly_trends: list[MonthlyTrend]
    recent_activity: list[RecentRecord]


class AuditLogOut(BaseModel):
    id: int
    actor_id: int
    actor_email: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    payload: Optional[dict]
    timestamp: str

    model_config = {"from_attributes": True}
