"""Initial migration - create all tables

Revision ID: 001_initial
Revises:
Create Date: 2026-04-02

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums
    user_role = sa.Enum("viewer", "analyst", "admin", name="user_role")
    record_type = sa.Enum("income", "expense", name="record_type")
    record_category = sa.Enum(
        "salary", "revenue", "investment", "operations",
        "marketing", "infrastructure", "payroll", "tax", "compliance", "other",
        name="record_category",
    )

    # Users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", user_role, nullable=False, server_default="viewer"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Financial records table
    op.create_table(
        "financial_records",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("type", record_type, nullable=False),
        sa.Column("category", record_category, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("record_date", sa.Date, nullable=False),
        sa.Column("reference_number", sa.String(100), nullable=True, index=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_by", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("updated_by", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Audit logs table — append-only, never modified
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("actor_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("action", sa.String(50), nullable=False, index=True),
        sa.Column("resource_type", sa.String(100), nullable=False, index=True),
        sa.Column("resource_id", sa.String(100), nullable=True, index=True),
        sa.Column("payload", sa.JSON, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("financial_records")
    op.drop_table("users")
    sa.Enum(name="user_role").drop(op.get_bind())
    sa.Enum(name="record_type").drop(op.get_bind())
    sa.Enum(name="record_category").drop(op.get_bind())
