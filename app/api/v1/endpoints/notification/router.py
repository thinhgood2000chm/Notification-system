from fastapi import APIRouter
from app.api.v1.endpoints.notification import view as view_root_router
router = APIRouter()


router.include_router(router=view_root_router.router,)
