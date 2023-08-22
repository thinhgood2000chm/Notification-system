from typing import List

from bson import ObjectId
from pydantic import BaseModel, Field

from app.api.v1.endpoints.activity.schema import WatcherDocument
from app.model.base import Base, PyObjectId


class WatcherStatus(BaseModel):
    watcher_id: str = Field(..., description='id watcher được tag')
    status: bool = Field(..., description='trang thái thông báo đã được watcher xem hay chưa </br> '
                                          '`False`: chưa được xem</br>'
                                          '`True`: đã được xem qua')


class NotificationResponse(Base):
    id: PyObjectId = Field(..., alias="_id")
    content: str = Field(..., nullable=True, description='Nội dung activity')
    watcher_noti_status: WatcherStatus = Field(..., description='id của watcher và trạng thái của noti')
    watcher_created_activity_document: WatcherDocument = Field(None, description='Thông tin người tạo')

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}


class CreateNotificationResponse(Base):
    id: PyObjectId = Field(..., alias="_id")
    content: str = Field(..., nullable=True, description='Nội dung activity')
    watcher_noti_status: List[WatcherStatus] = Field(..., description='id của watcher và trạng thái của noti')
    watcher_created_activity_document: WatcherDocument = Field(None, description='Thông tin người tạo')

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}


class NotificationRequest(BaseModel):
    content: str = Field(..., nullable=True, description='Nội dung activity')


class UpdateNotificationRequest(BaseModel):
    watcher_id: str = Field(..., description='id watcher')


class NumberNotificationResponse(BaseModel):
    number_notification: int = Field(..., description="Số lượng thông báo mới ( chưa đọc ) ")
