from datetime import date, datetime
from http.client import HTTPException
from typing import Union

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase  # noqa

from app.api.v1.setting.function import http_exception
from app.library.constant.function import DATETIME_FORMAT, PAGING_LIMIT


def datetime_to_str(_time: datetime, _format=DATETIME_FORMAT, default='') -> str:
    try:
        return _time.strftime(_format)
    except (ValueError, TypeError):
        return default


def datetime_to_date(datetime_input: datetime, default=None) -> date:
    try:
        return datetime_input.date()
    except (ValueError, TypeError):
        return default


def convert_str_to_int(data: str) -> Union[int, HTTPException]:
    try:
        return int(data)
    except ValueError:
        return http_exception(description=f"some error when convert {data} to int")


def is_valid_object_id(id: str):
    try:
        object_id = ObjectId(id)
        return object_id
    except InvalidId:
        return http_exception(description='invalid id')


def paging(
        query_param_for_paging: str,
        database_name: str,
        key_query: str,
        value_query: Union[str, dict],
        db: AsyncIOMotorDatabase,
        show_value: dict = None,  # sau khi query sẽ hiển thị những field nào, mặc định hiển thị hết
        sort: int = 1  # sort : -1 descending, 1 ascending
):
    object_id = is_valid_object_id(query_param_for_paging)
    if show_value is None:
        show_value = {}
    query_greater_than_or_less_than = "$gt"  # query lớn hơn
    if sort == -1:
        query_greater_than_or_less_than = "$lt"  # query bé hơn

    if not query_param_for_paging:
        cursor = db[database_name].find({key_query: value_query}, show_value).sort("_id", sort).limit(PAGING_LIMIT)
    else:
        cursor = db[database_name].find(
            {
                key_query: value_query,
                "_id": {
                    query_greater_than_or_less_than: object_id
                }
            },
            show_value
        ).sort("_id", sort).limit(PAGING_LIMIT)

    return cursor


def paging_aggregation(
        query_param_for_paging: str,
        database_name: str,
        key_query: str,
        value_query: Union[str, dict],
        db: AsyncIOMotorDatabase,
        foreign_table: str = "None",
        local_field: str = "None",
        foreign_field: str = "None",
        show_value: dict = None,  # sau khi query sẽ hiển thị những field nào, mặc định hiển thị hết
        sort: int = 1  # sort : -1 descending, 1 ascending
):
    object_id = is_valid_object_id(query_param_for_paging)

    query_greater_than_or_less_than = "$gt"  # query lớn hơn
    if sort == -1:
        query_greater_than_or_less_than = "$lt"  # query bé hơn

    cursor = db[database_name].aggregate(
        [
            {
                "$match": {
                    "$and": [{key_query: value_query}, {"_id": {query_greater_than_or_less_than: object_id}}]
                }
            } if query_param_for_paging else {
                "$match": {key_query: value_query}
            },
            {
                "$lookup": {
                    "from": foreign_table,
                    'localField': local_field,
                    'foreignField': foreign_field,
                    "as": f'{foreign_table}_document'
                }
            },
            {"$project": show_value} if show_value else {'$unset': f"{show_value}"},
            {"$sort": {"_id": sort}},
            {"$limit": PAGING_LIMIT}
        ]
    )

    return cursor
