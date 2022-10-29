from fastapi import APIRouter
from app.api.v1.endpoints.watcher import view as watcher_view
router = APIRouter()

router.include_router(router=watcher_view.router)
