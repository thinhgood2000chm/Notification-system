from fastapi import APIRouter
from app.api.v1.endpoints.activity import view as activity_view
router = APIRouter()

router.include_router(router=activity_view.router)
