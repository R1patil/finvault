# FinVault API

> **Compliant Finance Record Management Backend**
> A role-based, audit-first financial data system built for the Zorvyn Backend Developer Intern assessment.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-3ECF8E?style=flat&logo=supabase)](https://supabase.com)
[![Deployed](https://img.shields.io/badge/Deployed-Render-46E3B7?style=flat&logo=render)](https://render.com)

---

## Live API

| Resource | URL |
|---|---|
| **Base URL** | `https://finvault-api.onrender.com` |
| **Interactive Docs** | `https://finvault-api.onrender.com/docs` |
| **ReDoc** | `https://finvault-api.onrender.com/redoc` |
| **Health Check** | `https://finvault-api.onrender.com/health` |

> **Note:** Render free tier spins down after inactivity — first request may take ~30 seconds to cold start.

---

## Design Philosophy

Zorvyn's core product is compliance infrastructure. This backend reflects that same principle — every design decision is made with **auditability, access control, and data integrity** as first-class concerns, not afterthoughts.

Three principles guide this implementation:

1. **Compliance-first data model** — Financial records are never hard-deleted. Every soft delete is timestamped with who did it and when. This satisfies the immutability requirement in SOC 2 and RBI audit frameworks.

2. **Role enforcement at the service layer** — Access control is not just middleware — it is wired into every service call. A Viewer cannot create a record even if they craft a raw HTTP request; the dependency injection chain rejects it before business logic runs.

3. **Append-only audit trail** — Every state-changing operation (create, update, delete, login, role change) writes an immutable `AuditLog` row in the same database transaction. If the operation fails, the audit log is rolled back too — ensuring the trail is always accurate.

---

## Architecture

```
finvault/
├── app/
│   ├── main.py                  # FastAPI app + lifespan
│   ├── core/
│   │   ├── config.py            # Pydantic settings (env vars)
│   │   ├── database.py          # Async SQLAlchemy engine + session
│   │   └── security.py          # JWT, bcrypt, role dependency factory
│   ├── models/
│   │   ├── user.py              # User + UserRole enum
│   │   ├── financial_record.py  # FinancialRecord + soft delete fields
│   │   └── audit_log.py         # Append-only AuditLog
│   ├── schemas/
│   │   ├── user.py              # Pydantic I/O schemas
│   │   ├── financial_record.py  # Record schemas + filters + pagination
│   │   └── dashboard.py         # Summary + audit log output schemas
│   ├── services/
│   │   ├── record_service.py    # CRUD business logic + audit writes
│   │   ├── dashboard_service.py # Aggregation queries
│   │   └── audit_service.py     # Centralized audit log writer
│   └── api/v1/endpoints/
│       ├── auth.py              # Login, register, /me
│       ├── users.py             # Admin user management
│       ├── records.py           # Financial record CRUD
│       └── dashboard.py         # Summary + audit log endpoints
├── alembic/                     # Database migrations
├── scripts/seed.py              # Seed admin + sample data
├── render.yaml                  # One-click Render deployment
└── requirements.txt
```

**Key architectural choices:**
- **Async throughout** — `asyncpg` + `SQLAlchemy async` for non-blocking I/O under load
- **Dependency injection for auth** — `require_roles("admin", "analyst")` is a factory that returns a FastAPI `Depends` — clean, composable, testable
- **Service layer isolation** — endpoints never touch the DB directly; all logic lives in services
- **Single transaction per request** — audit log writes happen inside the same DB transaction as the operation they log

---

## Role Permission Matrix

| Action | Viewer | Analyst | Admin |
|--------|--------|---------|-------|
| Login / view own profile | ✅ | ✅ | ✅ |
| View financial records | ✅ | ✅ | ✅ |
| View dashboard summary | ✅ | ✅ | ✅ |
| Create financial records | ❌ | ✅ | ✅ |
| Update financial records | ❌ | ❌ | ✅ |
| Delete (soft) financial records | ❌ | ❌ | ✅ |
| List / manage users | ❌ | ❌ | ✅ |
| View audit logs | ❌ | ❌ | ✅ |

---

## API Reference

### Authentication

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/v1/auth/register` | Self-register (always VIEWER) | Public |
| `POST` | `/api/v1/auth/login` | Get JWT token | Public |
| `GET` | `/api/v1/auth/me` | Current user profile | Any role |

### Users (Admin only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/users` | List users (filter by role/status) |
| `POST` | `/api/v1/users` | Create user with any role |
| `GET` | `/api/v1/users/{id}` | Get user by ID |
| `PATCH` | `/api/v1/users/{id}` | Update role or active status |

### Financial Records

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/records` | Analyst, Admin | Create record |
| `GET` | `/api/v1/records` | All roles | List with filters + pagination |
| `GET` | `/api/v1/records/{id}` | All roles | Get single record |
| `PATCH` | `/api/v1/records/{id}` | Admin | Update record |
| `DELETE` | `/api/v1/records/{id}` | Admin | Soft delete (archived, never gone) |

**Supported filters on `GET /api/v1/records`:**
- `type` — `income` or `expense`
- `category` — `salary`, `revenue`, `investment`, `operations`, `marketing`, `infrastructure`, `payroll`, `tax`, `compliance`, `other`
- `date_from` / `date_to` — ISO date range
- `min_amount` / `max_amount` — decimal range
- `page` / `page_size` — pagination (default 1 / 20, max page_size 100)

### Dashboard & Analytics

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/v1/dashboard/summary` | All roles | Full dashboard: totals, category breakdown, monthly trends, recent activity |
| `GET` | `/api/v1/dashboard/audit-logs` | Admin | Immutable audit trail (filterable) |

---

## Data Models

### Financial Record
```json
{
  "id": 1,
  "amount": "500000.00",
  "type": "income",
  "category": "revenue",
  "description": "Q1 SaaS revenue",
  "record_date": "2026-01-15",
  "reference_number": null,
  "created_by": 1,
  "created_at": "2026-04-02T08:00:00Z",
  "updated_at": "2026-04-02T08:00:00Z"
}
```

### Dashboard Summary (excerpt)
```json
{
  "total_income": "1870000.00",
  "total_expense": "259500.00",
  "net_balance": "1610500.00",
  "record_count": 10,
  "income_by_category": [
    { "category": "revenue", "total": "1870000.00", "count": 3 }
  ],
  "monthly_trends": [
    { "year": 2026, "month": 1, "month_label": "Jan", "income": "620000.00", "expense": "107000.00", "net": "513000.00" }
  ],
  "recent_activity": [...]
}
```

### Audit Log Entry
```json
{
  "id": 42,
  "actor_id": 1,
  "actor_email": "admin@finvault.io",
  "action": "UPDATE",
  "resource_type": "financial_record",
  "resource_id": "7",
  "payload": {
    "before": { "amount": "85000.00", "category": "payroll" },
    "after": { "amount": "90000.00" }
  },
  "timestamp": "2026-04-02T09:15:30Z"
}
```

---

## Local Setup

### Prerequisites
- Python 3.11+
- A Supabase project (free tier works)

### 1. Clone and install
```bash
git clone https://github.com/R1patil/finvault.git
cd finvault
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env — add your Supabase DATABASE_URL and generate a SECRET_KEY:
# openssl rand -hex 32
```

Your `DATABASE_URL` from Supabase looks like:
```
postgresql+asyncpg://postgres.[ref]:[password]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
```

### 3. Run migrations
```bash
alembic upgrade head
```

### 4. Seed sample data
```bash
python scripts/seed.py
```
This creates three test users:
| Email | Password | Role |
|-------|----------|------|
| `admin@finvault.io` | `Admin@1234` | Admin |
| `analyst@finvault.io` | `Analyst@1234` | Analyst |
| `viewer@finvault.io` | `Viewer@1234` | Viewer |

### 5. Run the server
```bash
uvicorn app.main:app --reload
```
Visit `http://localhost:8000/docs` for the interactive Swagger UI.

---

## Deployment on Render

1. Push to GitHub
2. Create a new **Web Service** on [render.com](https://render.com) → connect your repo
3. Render auto-detects `render.yaml`
4. In Render dashboard → **Environment** → add:
   - `DATABASE_URL` — your Supabase connection string
   - `SECRET_KEY` — `openssl rand -hex 32`
5. Deploy → run migrations via Render Shell: `alembic upgrade head`
6. Run seed: `python scripts/seed.py`

---

## Assumptions & Tradeoffs

| Decision | Rationale |
|---|---|
| **Soft delete only** | Financial records must be traceable. Hard deletes violate audit trail integrity (SOC 2, RBI requirement). Deleted records remain in DB with `is_deleted=True`, `deleted_at`, and `deleted_by`. |
| **Analyst can create, not update/delete** | Analysts generate records (data entry) but shouldn't unilaterally modify committed entries — that's an admin responsibility matching typical finance team segregation of duties. |
| **Self-registration always gives VIEWER** | Prevents privilege escalation via the public endpoint. Role elevation requires an admin action, which is logged. |
| **Audit log in same transaction** | If the operation fails, the audit entry is rolled back. This prevents ghost audit entries for failed operations. |
| **Async SQLAlchemy + asyncpg** | FinTech systems handle concurrent reads from dashboards. Async I/O prevents thread starvation under load. |
| **JWT over sessions** | Stateless — suitable for a service that may scale horizontally or be consumed by a mobile/frontend client. |
| **Supabase over self-hosted Postgres** | Managed infrastructure with built-in connection pooling, SSL, and backups — appropriate for a system handling financial data. |

---

## What's Not Included (and Why)

- **Rate limiting** — would add with `slowapi` in production; excluded to keep the assessment scope clean
- **Email verification** — not required by the spec; easily added with a `is_verified` column + SMTP integration
- **Refresh tokens** — single-token with 24h expiry is sufficient for an assessment context
- **Unit tests** — the service layer is fully isolated and straightforward to test with `pytest-asyncio` + a test DB

---

*Built by Rahul Patil — Backend Developer Intern Assessment, Zorvyn FinTech Pvt. Ltd.*
