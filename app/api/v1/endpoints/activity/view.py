import re
from datetime import datetime

from aioredis import Redis
from fastapi import APIRouter, Depends, File, Form, Path, Query, UploadFile
from starlette.status import HTTP_200_OK, HTTP_201_CREATED

from app.api.v1.dependency.authentication import get_current_user, get_system
from app.api.v1.endpoints.activity.schema import (
    ActivityByDayResponse, CreateActivityByDayResponse
)
from app.api.v1.setting.event import service_file
from app.api.v1.setting.function import (
    http_exception, open_api_standard_responses
)
from app.library.function import (
    datetime_to_date, is_valid_object_id, paging_aggregation
)
from app.model.base import FailResponse, PyObjectId, ResponseData, db
from app.model.redis import redis_pool

router = APIRouter()


@router.post(
    path="/activity/",
    name="activity: Create new activity",
    description='Create new activity',
    status_code=HTTP_201_CREATED,
    responses=open_api_standard_responses(
        success_status_code=HTTP_201_CREATED,
        success_response_model=ResponseData[CreateActivityByDayResponse],
        fail_response_model=FailResponse
    )
)
async def create_new_activity(
        file: UploadFile = File(None),
        content: str = Form(None, description="content when watcher comment in topic"),
        watcher_id: str = Form(..., description="id watcher create activity"),
        group_profile_id: str = Form(...),
        system_name: dict = Depends(get_system),
        redis: Redis = Depends(redis_pool)
):
    group_profile = await db.group_profile.find_one({"group_profile_id": group_profile_id, "created_by": system_name})
    if not group_profile:
        return http_exception(description=f"group profile id = {group_profile_id} does not exist")

    watcher = await db.watcher.find_one({"watcher_id": watcher_id})
    if not watcher:
        return http_exception(description=f"watcher_id = {watcher_id} not exist")

    # đối với những watcher ko có trong group_profile nếu được phép comment thì
    # khi comment sẽ được add vào member của group
    if watcher_id not in group_profile['watcher_ids']:
        await db.group_profile.find_one_and_update(
            {"group_profile_id": group_profile_id},
            {
                '$push': {'watcher_ids': watcher_id},
                '$set': {'updated_at': datetime.now()}
            }
        )

    # thêm white space ở cuối content để trường hợp tag user ở cuối câu ko có dấu " " thì regex ko tìm được
    content = f'{content} '
    activity = {'group_profile_id': group_profile_id, 'content': content}
    tag_users = re.findall(r'@(.*?)[\s@]', content)
    tag_users = [tag_user.strip() for tag_user in tag_users if tag_user != watcher['username']]

    if not tag_users or "all" in tag_users:
        activity['tag_users'] = ['@all']
    else:
        cursor = db.watcher.find({'username': {"$in": tag_users}})
        list_watcher_tag = await cursor.to_list(None)

        activity['tag_users'] = \
            [watcher['watcher_id']
             for watcher in list_watcher_tag if watcher['watcher_id'] in group_profile['watcher_ids']]

    uuid_and_file_url = None
    if file:
        await file.seek(0)
        file_data_stream = await file.read()
        is_success, uuid_and_file_url = await service_file.upload_file(file=file_data_stream)

        if not is_success:
            return http_exception(description="Get some error when upload file to service")

    activity['file_uuid'] = uuid_and_file_url['uuid'] if uuid_and_file_url else None
    activity['file_url'] = uuid_and_file_url['file_url'] if uuid_and_file_url else None
    activity['file_name'] = file.filename if file else None

    activity['watcher_id'] = watcher['watcher_id']
    activity['created_by'] = watcher['username']
    activity['updated_by'] = watcher['username']
    activity['created_at'] = datetime.now()
    activity['updated_at'] = datetime.now()

    new_activity = await db.activity.insert_one(activity)

    if new_activity.inserted_id:
        await db.group_profile.update_one(
            {"group_profile_id": group_profile_id},
            {'$push': {'activity_ids': PyObjectId.validate(new_activity.inserted_id)}}
        )
    else:
        return http_exception(description="Get some error when create activity")

    # tạo mới thông báo
    list_new_notification = []

    watcher_ids_in_tag = None

    if '@all' not in activity['tag_users']:
        # nếu được tag thì chỉ những người được tag sẽ nhận được thông báo ai đã tag
        watcher_ids_in_tag_cursor = db.watcher.find(
            {"$and": [
                {"watcher_id": {"$in": activity['tag_users']}},
                {"watcher_id": {"$ne": watcher_id}}  # tìm watcher ngoại trừ người tạo activity
            ]}
        )
        watcher_ids_in_tag = await watcher_ids_in_tag_cursor.to_list(None)
    # nêu ko được tag thì tất cả watcher trong group ngoại trừ người tạo
    #  activity['tag_users'] có giá trị là [@all] nên ko ảnh hưởng
    watcher_ids_not_in_tag_cursor = db.watcher.find(
        {"$and": [
            {"watcher_id": {"$in": group_profile['watcher_ids']}},
            {"watcher_id": {"$nin": activity['tag_users']}},
            {"watcher_id": {"$ne": watcher_id}}  # tìm watcher ngoại trừ người tạo activity
        ]}
    )

    watcher_ids_not_in_tag = await watcher_ids_not_in_tag_cursor.to_list(None)
    watcher_ids = []
    if watcher_ids_not_in_tag:
        watcher_noti_status_not_in_tag = [
            {
                "watcher_id": watcher['watcher_id'],
                "status": False
            } for watcher in watcher_ids_not_in_tag
        ]
        list_new_notification.append(
            {
                'content': f"{watcher['username']} vừa bình luận",
                'watcher_noti_status': watcher_noti_status_not_in_tag,
                "activity_id": new_activity.inserted_id,
                "watcher_created_activity": watcher_id,
                "created_by": group_profile['created_by'],
                "updated_by": group_profile['created_by'],
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        )
        watcher_ids.extend([watcher['watcher_id'] for watcher in watcher_ids_not_in_tag])
    if watcher_ids_in_tag:

        watcher_noti_status_in_tag = [
            {
                "watcher_id": watcher['watcher_id'],
                "status": False
            } for watcher in watcher_ids_in_tag
        ]
        list_new_notification.append(
            {
                'content': f"{watcher['username']} vừa nhắc đến bạn trong group_profile id = {group_profile_id}",
                'watcher_noti_status': watcher_noti_status_in_tag,
                "activity_id": new_activity.inserted_id,
                "watcher_created_activity": watcher_id,
                "created_by": group_profile['created_by'],
                "updated_by": group_profile['created_by'],
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        )

        watcher_ids.extend([watcher['watcher_id'] for watcher in watcher_ids_in_tag])

    await db.notification.insert_many(list_new_notification)

    # lưu lại số thông báo chưa đọc trong redis
    # watcher_id__new_number_noti = {}
    number_noti_not_reads = await redis.mget(watcher_ids)

    for index, watcher_id in enumerate(watcher_ids):
        value_number_noti = number_noti_not_reads[index]
        # chỉ cập nhật redis nếu watcher đó đang online( nếu offline hoặc chưa có dữ liệu thì redis sẽ bằng None)
        if value_number_noti:
            await redis.incr(watcher_id)

    # await redis.mset(watcher_id__new_number_noti)
    activity['watcher_created_acitivity_document'] = {
        "watcher_id": watcher['watcher_id'],
        "username": watcher['username'],
        "avatar_url": watcher['avatar_url']
    }
    data = {
        "created_day": activity['created_at'],
        "activities": activity
    }
    return ResponseData[CreateActivityByDayResponse](**{"data": data})


@router.get(
    path="/{group_profile_id}/activity/",
    name="activity: Get activity of group profile",
    description='Get activity of group profile',
    status_code=HTTP_200_OK,
    responses=open_api_standard_responses(
        success_status_code=HTTP_200_OK,
        success_response_model=ResponseData[list[ActivityByDayResponse]],
        fail_response_model=FailResponse
    )
)
async def get_all_activity(
        group_profile_id: str = Path(..., description="id of group_profile"),
        last_activity_id: str = Query(None, description="last _id of activity in list"),
        watcher: dict = Depends(get_current_user)
):
    group_profile = await db.group_profile.find_one({"group_profile_id": group_profile_id})
    if not group_profile:
        return http_exception(description=f"group_profile_id = {group_profile_id} does not exist")

    cursor = paging_aggregation(
        query_param_for_paging=last_activity_id,
        database_name="activity",
        key_query="group_profile_id",
        value_query=group_profile_id,
        db=db,
        foreign_table='watcher',
        local_field="watcher_id",
        foreign_field="watcher_id",
        sort=-1
    )
    activities = []

    if cursor:
        activities = await cursor.to_list(None)

    day__activities_response = {}
    for activity in activities:
        if activity['watcher_document']:
            activity['watcher_created_acitivity_document'] = activity['watcher_document'][0]

        created_at_in_date = datetime_to_date(activity['created_at'])
        if created_at_in_date not in day__activities_response:
            day__activities_response[created_at_in_date] = []
        day__activities_response[created_at_in_date].append(activity)

    data_response = {"data": []}
    for key, value in day__activities_response.items():
        data_response['data'].append({"created_day": key, "activities": value})

    return ResponseData[list[ActivityByDayResponse]](**data_response)


@router.delete(
    path="/{group_profile_id}/activity/{activity_id}",
    name="activity: Delete acitivity",
    description='Delete activity',
    status_code=HTTP_200_OK,
    responses=open_api_standard_responses(
        success_status_code=HTTP_200_OK,
        fail_response_model=FailResponse
    )
)
async def delete_activity(
        activity_id: str = Path(..., description='`_id` of activity'),
        group_profile_id: str = Path(..., description='`group_profile_id` of group '),
        system_name: str = Depends(get_system),
        redis: Redis = Depends(redis_pool)
):

    object_id = is_valid_object_id(activity_id)
    group_profile = await db.group_profile.find_one({"group_profile_id": group_profile_id, "created_by": system_name})
    if group_profile is None:
        return http_exception(description=f'group_profile_id = {group_profile_id} does not exist')
    activity = await db.activity.find_one_and_delete({"_id": object_id, "group_profile_id": group_profile_id})
    if activity is None:
        return http_exception(description="_id does not exist")

    notification_cursor = db.notification.find({'activity_id': object_id})
    notifications = await notification_cursor.to_list(None)
    watcher_ids = []
    for notification in notifications:
        watcher_ids.extend([watcher['watcher_id'] for watcher in notification['watcher_noti_status'] if not watcher['status']])

    number_noti_not_reads = await redis.mget(watcher_ids)

    for index, watcher_id in enumerate(watcher_ids):
        value_number_noti = number_noti_not_reads[index]
        if value_number_noti:
            await redis.decr(watcher_id)
    # await redis.mset(watcher_id__new_number_noti)

    # bên trên đã check tồn tại rồi nên bên dưới chỉ cần filter theo id để cập nhật
    await db.group_profile.update_one({"group_profile_id": group_profile_id}, {'$pull': {'activity_ids': activity_id}})
    return None
