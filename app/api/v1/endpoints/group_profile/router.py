from fastapi import APIRouter
from app.api.v1.endpoints.group_profile import view as group_view
router = APIRouter()

router.include_router(router=group_view.router)
