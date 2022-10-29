from fastapi import APIRouter

from app.api.v1.endpoints.notification import router as routers_test
from app.api.v1.endpoints.group_profile import router as routers_group
from app.api.v1.endpoints.watcher import router as routers_watcher
from app.api.v1.endpoints.activity import router as routers_activity

router = APIRouter()

router.include_router(router=routers_test.router, tags=["[NOTIFICATION]"])
router.include_router(router=routers_watcher.router, tags=["[WATCHER]"])
router.include_router(router=routers_group.router, tags=["[GROUP_PROFILE]"])
router.include_router(router=routers_activity.router, tags=["[ACTIVITY]"])



