from datetime import date, datetime
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field, HttpUrl

from app.library.function import datetime_to_str
from app.model.base import Base, PyObjectId


class WatcherDocument(BaseModel):
    watcher_id: str = Field(..., description="Id người tạo activity")
    username: str = Field(..., description="Tên watcher")
    avatar_url: str = Field(..., description="url avatar")


class ActivityResponse(Base):
    id: PyObjectId = Field(..., alias="_id")
    content: str = Field(..., nullable=True, description='Nội dung activity')
    file_uuid: Optional[str] = Field(..., nullable=True, description="Uuid file gửi lên")
    file_name: Optional[str] = Field(..., nullable=True, description="Tên file gửi lên")
    file_url: Optional[HttpUrl] = Field(..., nullable=True, description='Đường dẫn tải file từ minio')
    tag_users: list = Field(..., description="Các watcher_id được tag")
    watcher_created_acitivity_document: WatcherDocument = Field(..., description="thông tin người tạo")
    group_profile_id: str = Field(..., description="Id group profile")

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}


class ActivityByDayResponse(BaseModel):
    created_day: date = Field(..., example='dd/mm/YYYY', description='Thời gian khởi tạo')
    activities: list[ActivityResponse]

    class Config:
        json_encoders = {
            datetime: lambda dt: datetime_to_str(dt)
        }


class CreateActivityByDayResponse(BaseModel):
    created_day: date = Field(..., example='dd/mm/YYYY', description='Thời gian khởi tạo')
    activities: ActivityResponse

    class Config:
        json_encoders = {
            datetime: lambda dt: datetime_to_str(dt)
        }
