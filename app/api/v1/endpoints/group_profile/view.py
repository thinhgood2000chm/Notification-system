from datetime import datetime

from fastapi import APIRouter, Depends, Path, Query
from pymongo import ReturnDocument
from starlette.status import HTTP_200_OK, HTTP_201_CREATED

from app.api.v1.dependency.authentication import get_system
from app.api.v1.endpoints.group_profile.schema import (
    GroupProfileRequest, GroupProfileResponse, UpdateWatcherGroupProfileRequest
)
from app.api.v1.setting.function import (
    http_exception, open_api_standard_responses
)
from app.model.base import FailResponse, ResponseData, db

router = APIRouter()


@router.post(
    path="/group-profile/",
    name="group-profile: create new group profile",
    description='Create new group profile',
    status_code=HTTP_201_CREATED,
    responses=open_api_standard_responses(
        success_status_code=HTTP_201_CREATED,
        success_response_model=ResponseData[GroupProfileResponse],
        fail_response_model=FailResponse
    )
)
async def create_group_profile(
        group_profile: GroupProfileRequest,
        system_name: str = Depends(get_system)
):
    group_profile = group_profile.dict()
    group_profile["created_by"] = system_name
    group_profile["updated_by"] = system_name
    group_profile["created_at"] = datetime.now()
    group_profile["updated_at"] = datetime.now()
    group_profile["activity_ids"] = []

    exist_group_profile = await db.group_profile.find_one({"group_profile_id": group_profile['group_profile_id']})
    if exist_group_profile:
        return http_exception(description=f"group_profile_id = {exist_group_profile['group_profile_id']} is exist")

    if group_profile['watcher_ids']:
        cursor = db.watcher.find({"watcher_id": {"$in": group_profile['watcher_ids']}})
        watchers = await cursor.to_list(None)
        if len(watchers) != len(group_profile['watcher_ids']):
            list_watcher_id_in_db = [watcher["watcher_id"] for watcher in watchers]
            not_exist_watcher_id = []
            for watcher in group_profile['watcher_ids']:
                if watcher not in list_watcher_id_in_db:
                    not_exist_watcher_id.append(watcher)
            return http_exception(description=f"watcher_id = {not_exist_watcher_id} does not exist")

    await db.group_profile.insert_one(group_profile)

    return ResponseData[GroupProfileResponse](**{"data": group_profile})


@router.patch(
    path="/group-profile/{group_profile_id}",
    name="group-profile: Add or delete watcher in group profile",
    description='Add or delete watcher to group profile',
    status_code=HTTP_200_OK,
    responses=open_api_standard_responses(
        success_status_code=HTTP_200_OK,
        success_response_model=ResponseData[GroupProfileResponse],
        fail_response_model=FailResponse
    )
)
async def update_watcher_in_group_profile(
        watcher_ids: UpdateWatcherGroupProfileRequest,
        group_profile_id: str = Path(...),
        remove_watcher_flag: bool = Query(default=False, description="`True`: remove watcher, <br/>"
                                                                     "`False`: add watcher to group profile"),
        system_name: str = Depends(get_system)
):
    watcher_ids = watcher_ids.dict()
    if len(watcher_ids['watcher_ids']) != len(set(watcher_ids['watcher_ids'])):
        return http_exception(description="some watcher_id have same value")

    group_profile = await db.group_profile.find_one({"group_profile_id": group_profile_id, 'created_by': system_name})
    if group_profile is None:
        http_exception(description=f"group_profile_id = {group_profile_id} is not exist")

    cursor = db.watcher.find({"watcher_id": {"$in": watcher_ids['watcher_ids']}})
    list_watcher = await cursor.to_list(None)

    if len(list_watcher) != len(watcher_ids['watcher_ids']):
        list_watcher_id_in_db = [watcher["watcher_id"] for watcher in list_watcher]
        not_exist_watcher_id = []
        for watcher in watcher_ids['watcher_ids']:
            if watcher not in list_watcher_id_in_db:
                not_exist_watcher_id.append(watcher)
        return http_exception(description=f"watcher_id = {not_exist_watcher_id} does not exist")

    if not remove_watcher_flag:
        list_watcher_id_exist_in_group_profile = []
        for watcher_id in watcher_ids['watcher_ids']:
            if watcher_id in group_profile['watcher_ids']:
                list_watcher_id_exist_in_group_profile.append(watcher_id)

        if list_watcher_id_exist_in_group_profile:
            return http_exception(
                description=f"watcher_id = {list_watcher_id_exist_in_group_profile} "
                            f"already exist in group_profile_id = {group_profile_id}"
            )
        group_profile_after_update = await db.group_profile.find_one_and_update(
            {"group_profile_id": group_profile_id},
            {
                '$push': {'watcher_ids': {"$each": watcher_ids['watcher_ids']}},
                '$set': {'updated_at': datetime.now()}
            },
            return_document=ReturnDocument.AFTER
        )

    else:
        watcher_id_not_exist_in_group_profile = []
        for watcher_id in watcher_ids['watcher_ids']:
            if watcher_id not in group_profile['watcher_ids']:
                watcher_id_not_exist_in_group_profile.append(watcher_id)
        if watcher_id_not_exist_in_group_profile:
            return http_exception(description=f"watcher_id = {watcher_id_not_exist_in_group_profile} not exist in group profile")

        group_profile_after_update = await db.group_profile.find_one_and_update(
            {"group_profile_id": group_profile_id},
            {
                '$pull': {'watcher_ids': {"$in": watcher_ids['watcher_ids']}},
                '$set': {'updated_at': datetime.now()}
            },
            return_document=ReturnDocument.AFTER
        )

    return ResponseData[GroupProfileResponse](**{"data": group_profile_after_update})
