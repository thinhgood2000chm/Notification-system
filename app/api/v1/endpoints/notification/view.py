from datetime import datetime
from typing import List

from aioredis import Redis
from fastapi import APIRouter, Depends, Path, Query
from pymongo import ReturnDocument
from starlette.status import HTTP_200_OK

from app.api.v1.dependency.authentication import (
    EXPIRES_TIME, get_current_user, get_system
)
from app.api.v1.endpoints.notification.schema import (
    CreateNotificationResponse, NotificationRequest, NotificationResponse,
    NumberNotificationResponse, UpdateNotificationRequest
)
from app.api.v1.setting.function import (
    http_exception, open_api_standard_responses
)
from app.library.function import (
    convert_str_to_int, is_valid_object_id, paging_aggregation
)
from app.model.base import FailResponse, ResponseData, db
from app.model.redis import redis_pool

router = APIRouter()


@router.get(
    path="/notification/",
    name="notification: Get notification of watcher",
    description='Get notification of watcher',
    status_code=HTTP_200_OK,
    responses=open_api_standard_responses(
        success_status_code=HTTP_200_OK,
        success_response_model=ResponseData[List[NotificationResponse]],
        fail_response_model=FailResponse
    )
)
async def get_all_notification_of_watcher(
        last_notification_id: str = Query(None, description="last id of list notification"),
        watcher_id: str = Query(..., description="id watcher"),
        system_name: dict = Depends(get_system),
):
    watcher = await db.watcher.find_one({"watcher_id": watcher_id})
    if watcher is None:
        return http_exception(description=f"watcher_id = {watcher_id} is not exist")

    notification_cursor = paging_aggregation(
        query_param_for_paging=last_notification_id,
        database_name="notification",
        key_query="watcher_noti_status.watcher_id",
        value_query=watcher['watcher_id'],
        db=db,
        foreign_table='watcher',
        local_field="watcher_created_activity",
        foreign_field="watcher_id",
        show_value={
            "_id": 1,
            "content": 1,
            "created_by": 1,
            "updated_by": 1,
            "created_at": 1,
            "updated_at": 1,
            "watcher_document": 1,
            "watcher_noti_status": {
                "$filter": {
                    "input": "$watcher_noti_status",
                    "as": "watcher_noti_status",
                    "cond": {
                        "$eq": ["$$watcher_noti_status.watcher_id", watcher['watcher_id']]
                    }
                }
            }
        },
        sort=-1
    )

    list_notification = await notification_cursor.to_list(None)

    for notification in list_notification:
        notification['watcher_created_activity_document'] = \
            notification['watcher_document'][0] if notification['watcher_document'] else None
        notification['watcher_noti_status'] = \
            notification['watcher_noti_status'][0] if notification['watcher_noti_status'] else None
    return ResponseData[List[NotificationResponse]](**{"data": list_notification})


@router.patch(
    path="/notification/{notification_id}",
    name="notification: update notification status",
    description='Update notification status',
    status_code=HTTP_200_OK,
    responses=open_api_standard_responses(
        success_status_code=HTTP_200_OK,
        success_response_model=ResponseData[NotificationResponse],
        fail_response_model=FailResponse
    )
)
async def update_status_noti(
        watcher: UpdateNotificationRequest,
        notification_id: str = Path(..., description="id of notification"),
        system_name: dict = Depends(get_system),
        redis: Redis = Depends(redis_pool)
):
    watcher = watcher.dict()
    watcher = await db.watcher.find_one({"watcher_id": watcher['watcher_id']}, {'watcher_id': 1, '_id': 0})

    object_id = is_valid_object_id(notification_id)

    notification = await db.notification.find_one_and_update(
        {
            "_id": object_id,
            "watcher_noti_status": {
                "$elemMatch": {
                    "watcher_id": watcher['watcher_id'],
                    "status": False
                }
            }
        },
        {
            "$set": {
                'watcher_noti_status.$.status': True
            }
        },
        return_document=ReturnDocument.AFTER,
        projection={
            "_id": 1,
            "content": 1,
            "created_by": 1,
            "updated_by": 1,
            "created_at": 1,
            "updated_at": 1,
            "watcher_created_activity": 1,
            "watcher_noti_status": {
                "$elemMatch": {
                    "watcher_id": watcher['watcher_id']
                }
            }
        }
    )

    if notification is None:
        return http_exception(
            description=f"notification_id = {notification_id} does not exist or already update status"
        )

    # lookup ko dùng được với update nên cần tìm lại người tạo activity để lấy thông tin
    if notification['watcher_created_activity']:
        watcher_created_activity = await db.watcher.find_one({"watcher_id": notification['watcher_created_activity']})

        notification['watcher_created_activity_document'] = {
            "watcher_id": watcher_created_activity['watcher_id'],
            "username": watcher_created_activity['username'],
            "avatar_url": watcher_created_activity['avatar_url']
        }
    else:
        notification['watcher_created_activity_document'] = None

    notification['watcher_noti_status'] = \
        notification['watcher_noti_status'][0] if notification['watcher_noti_status'] else None

    number_noti_not_read = await redis.get(watcher['watcher_id'])
    if number_noti_not_read is None:
        return http_exception(description=f"cache of watcher_id = {watcher['watcher_id']} is not exist")
    if convert_str_to_int(number_noti_not_read) >= 1:
        await redis.decr(watcher['watcher_id'])

    return ResponseData[NotificationResponse](**{"data": notification})


# SỬ DỤNG CHO HỆ THỐNG GỬI THÔNG BÁO TỚI TẤT CẢ CÁC WATCHER CÓ TRONG HỆ THỐNG ( KO PHỤ THUỘC VÀO GROUP_PROFILE)

@router.post(
    path="/notification/",
    name="notification: Create notification",
    description='Create notification',
    status_code=HTTP_200_OK,
    responses=open_api_standard_responses(
        success_status_code=HTTP_200_OK,
        success_response_model=ResponseData[CreateNotificationResponse],
        fail_response_model=FailResponse
    )
)
async def create_notification(
        notification_request: NotificationRequest,
        system_name: str = Depends(get_system),
        redis: Redis = Depends(redis_pool)
):
    notification_request = notification_request.dict()
    notification_request['created_by'] = system_name
    notification_request['created_at'] = datetime.now()
    notification_request['updated_by'] = system_name
    notification_request['updated_at'] = datetime.now()
    notification_request['watcher_created_activity'] = None

    watchers_cursor = db.watcher.find({}, {"watcher_id": 1, "_id": 0})
    watchers = await watchers_cursor.to_list(None)
    watcher_noti_status = [
        {
            "watcher_id": watcher['watcher_id'],
            "status": False
        } for watcher in watchers
    ]
    notification_request['watcher_noti_status'] = watcher_noti_status
    await db.notification.insert_one(notification_request)

    # watcher_id__new_number_noti = {}

    watcher_ids = [watcher['watcher_id'] for watcher in watchers]

    number_noti_not_reads = await redis.mget(watcher_ids)
    for index, watcher_id in enumerate(watcher_ids):
        value_number_noti = number_noti_not_reads[index]
        if value_number_noti:
            await redis.incr(watcher_id)

    return ResponseData[CreateNotificationResponse](**{"data": notification_request})


@router.get(
    path="/notification/number/",
    name="notification: Get number notification not read",
    description='Create notification',
    status_code=HTTP_200_OK,
    responses=open_api_standard_responses(
        success_status_code=HTTP_200_OK,
        success_response_model=ResponseData[NumberNotificationResponse],
        fail_response_model=FailResponse
    )
)
async def get_number_notification(
        redis: Redis = Depends(redis_pool),
        watcher: dict = Depends(get_current_user)
):
    number_notification = await redis.get(watcher['watcher_id'])
    if number_notification is None:
        notification_of_watcher_cursor = db.notification.find({
            "watcher_noti_status": {
                "$elemMatch": {
                    "watcher_id": watcher['watcher_id'],
                    "status": False
                }
            }
        },
        )
        notification_of_watcher = await notification_of_watcher_cursor.to_list(None)
        number_notification = len(notification_of_watcher)
        # khi watcher online thì lưu số lượng thông báo vào redis và chỉ set thời gian ở đây
        # những chỗ khác ko được đụng tới thời gian sống của redis
        await redis.setex(watcher['watcher_id'], EXPIRES_TIME * 60, number_notification)
        # thời gian trong redis tính bằng giây còn jwt tính bằng phút nên nhân thêm 60 để 2 thời gian bằng nhau

    name__number_noti = {"number_notification": number_notification}

    return ResponseData[NumberNotificationResponse](**{"data": name__number_noti})
