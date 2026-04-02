from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.records import router as records_router
from app.api.v1.endpoints.dashboard import router as dashboard_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(users_router)
router.include_router(records_router)
router.include_router(dashboard_router)
