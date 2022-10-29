from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Path, Query
from fastapi.encoders import jsonable_encoder
from starlette.status import HTTP_200_OK, HTTP_201_CREATED

from app.api.v1.dependency.authentication import (
    create_access_token, get_system
)
from app.api.v1.endpoints.watcher.schema import (
    DeleteWacherRequest, UserTokenResponse, WatcherIdRequest,
    WatcherResponseSchema, WatcherSchema
)
from app.api.v1.setting.function import (
    http_exception, open_api_standard_responses
)
from app.library.function import paging
from app.model.base import FailResponse, ResponseData, db

router = APIRouter()


@router.post(
    path="/watcher/",
    name="watcher: create new watcher",
    description='Tạo mới một watcher',
    status_code=HTTP_201_CREATED,
    responses=open_api_standard_responses(
        success_status_code=HTTP_201_CREATED,
        success_response_model=ResponseData[WatcherResponseSchema],
        fail_response_model=FailResponse
    )
)
async def create_watcher(
        watcher: WatcherSchema,
        system_name: str = Depends(get_system)
):
    watcher = watcher.dict()
    watcher["created_by"] = system_name
    watcher["updated_by"] = system_name
    watcher["created_at"] = datetime.now()
    watcher["updated_at"] = datetime.now()

    exist_watcher = await db.watcher.find_one(
        {"$or": [{"watcher_id": watcher['watcher_id']}, {'username': watcher['username']}]}
    )
    if exist_watcher:
        return http_exception(description="watcher is already exist")
    await db.watcher.insert_one(watcher)
    return ResponseData[WatcherResponseSchema](**{"data": watcher})


@router.post(
    path="/watchers/",
    name="watcher: create multi watcher",
    description='Create multi watcher',
    status_code=HTTP_201_CREATED,
    responses=open_api_standard_responses(
        success_status_code=HTTP_201_CREATED,
        success_response_model=ResponseData[list[WatcherResponseSchema]],
        fail_response_model=FailResponse),
)
async def create_multi_watcher(
        watchers: List[WatcherSchema],
        system_name: str = Depends(get_system)
):
    watchers = jsonable_encoder(watchers)
    list_watcher_id = [watcher['watcher_id'] for watcher in watchers]
    list_username = [watcher['username'] for watcher in watchers]
    if len(list_watcher_id) != len(set(list_watcher_id)):
        return http_exception(description="Some watcher_id is same data")
    cursor = db.watcher.find({"$or": [{"watcher_id": {"$in": list_watcher_id}}, {"username": {"$in": list_username}}]})
    exist_watchers = await cursor.to_list(None)

    if exist_watchers:
        return http_exception(
            description=f"watcher_id/watcher_username = {[exist_watcher['watcher_id'] + '/' + exist_watcher['username'] for exist_watcher in exist_watchers]} is already exist"
        )
    for watcher in watchers:
        watcher["created_by"] = system_name
        watcher["updated_by"] = system_name
        watcher["created_at"] = datetime.now()
        watcher["updated_at"] = datetime.now()

    await db.watcher.insert_many(watchers)
    return ResponseData[list[WatcherResponseSchema]](**{"data": watchers})


@router.delete(
    path="/watcher/{watcher_id}/",
    name="watcher:Delete watcher",
    description='Delete watcher',
    status_code=HTTP_200_OK,
    responses=open_api_standard_responses(
        success_status_code=HTTP_200_OK,
        fail_response_model=FailResponse),
)
async def delete_watcher(
        watcher_id: str = Path(...),
        system_name: str = Depends(get_system)
):
    cursor = db.group_profile.find({"watcher_ids": {"$elemMatch": {"$eq": watcher_id}}})
    watcher_in_profile = await cursor.to_list(None)
    if watcher_in_profile:
        return http_exception(description="Can't delete this watcher because watcher is in group profile")

    data = await db.watcher.find_one_and_delete({"watcher_id": watcher_id})
    if data is None:
        return http_exception(description=f"{watcher_id} is not exist")

    return None


@router.delete(
    path="/watchers/",
    name="watcher:Delete multi watcher",
    description='Delete multi watcher',
    status_code=HTTP_200_OK,
    responses=open_api_standard_responses(
        success_status_code=HTTP_200_OK,
        fail_response_model=FailResponse),
)
async def delete_multi_watcher(
        list_watcher_id: DeleteWacherRequest,
        system_name: str = Depends(get_system)
):
    list_watcher_id = jsonable_encoder(list_watcher_id)

    cursor = db.watcher.find({"watcher_id": {"$in": list_watcher_id['list_watcher_id']}})
    exist_watchers = await cursor.to_list(None)

    not_exist_watcher_id = []

    if len(exist_watchers) != len(list_watcher_id['list_watcher_id']):
        exist_watchers = [exist_watcher['watcher_id'] for exist_watcher in exist_watchers]
        for watcher in list_watcher_id['list_watcher_id']:
            if watcher not in exist_watchers:
                not_exist_watcher_id.append(watcher)
        return http_exception(description=f"watcher_ids = {not_exist_watcher_id} are not exist")

    await db.watcher.delete_many({"watcher_id": {"$in": list_watcher_id['list_watcher_id']}})

    return None


@router.get(
    path="/watcher/{watcher_id}/",
    name="watcher:Get watcher",
    description='Get watcher',
    status_code=HTTP_200_OK,
    responses=open_api_standard_responses(
        success_status_code=HTTP_200_OK,
        success_response_model=ResponseData[WatcherResponseSchema],
        fail_response_model=FailResponse),
)
async def get_watcher(
        watcher_id: str = Path(...),
        system_name: str = Depends(get_system)
):
    watcher_info = await db.watcher.find_one({"watcher_id": watcher_id})
    if watcher_info is None:
        return http_exception(description=f"watcher_id = {watcher_id} is not found")
    return ResponseData[WatcherResponseSchema](**{"data": watcher_info})


@router.post(
    path="/watcher/generate-token/",
    name="watcher: Generate token ",
    description='Generate token',
    status_code=HTTP_200_OK,
    responses=open_api_standard_responses(
        success_status_code=HTTP_200_OK,
        success_response_model=ResponseData[UserTokenResponse],
        fail_response_model=FailResponse),
)
async def generate_token(
        watcher_id: WatcherIdRequest,
        system_name: str = Depends(get_system)
):
    watcher_id = watcher_id.dict()
    watcher = await db.watcher.find_one({"watcher_id": watcher_id["watcher_id"]})
    if watcher is None:
        return http_exception(description=f"watcher_id = {watcher_id['watcher_id']} is not exist")
    watcher['token'] = await create_access_token(watcher["watcher_id"])
    return ResponseData[UserTokenResponse](**{"data": watcher})


@router.get(
    path="/watchers/{group_profile_id}/",
    name="watcher:Get all watcher of group profile",
    description='Get all watcher of group profile',
    status_code=HTTP_200_OK,
    responses=open_api_standard_responses(
        success_status_code=HTTP_200_OK,
        success_response_model=ResponseData[list[WatcherResponseSchema]],
        fail_response_model=FailResponse),
)
async def get_all_watchers_of_group(
        group_profile_id: str = Path(...),
        last_watcher_id: str = Query(None, description="last _id of watcher in list"),
        system_name: str = Depends(get_system)
):
    group_profile = await db.group_profile.find_one({"group_profile_id": group_profile_id, 'created_by': system_name})
    if not group_profile:
        return http_exception(description=f'group_profile_id = {group_profile_id} is not exist')

    if group_profile['watcher_ids'] is None:
        return http_exception(description='group_profile does not have member')

    # watchers_cursor = db.watcher.find({"watcher_id": {"$in": group_profile['watcher_ids']}})
    watchers_cursor = paging(
        query_param_for_paging=last_watcher_id,
        database_name="watcher",
        key_query="watcher_id",
        value_query={"$in": group_profile['watcher_ids']},
        db=db,
        sort=1)
    watchers = await watchers_cursor.to_list(None)

    return ResponseData[list[WatcherResponseSchema]](**{"data": watchers})
