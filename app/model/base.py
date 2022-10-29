import os
from datetime import datetime
from typing import Generic, TypeVar

import motor.motor_asyncio
from bson import ObjectId
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

from app.library.function import datetime_to_str

load_dotenv()

MONGO_DETAILS = \
    f"mongodb+srv://{os.getenv('USERNAME_DB')}:{os.getenv('PASSWORD_DB')}@cluster0.gc4d8sf.mongodb.net/?retryWrites=true&w=majority"

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
db = client.college

TypeX = TypeVar("TypeX")


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return str(ObjectId(v))

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class Base(BaseModel):
    created_by: str = Field(..., description="Được tạo bởi")
    updated_by: str = Field(..., description="Được cập nhật bởi")
    created_at: datetime = Field(..., example='dd/mm/YYYY HH:MM:SS', description='Thời gian khởi tạo')
    updated_at: datetime = Field(..., example='dd/mm/YYYY HH:MM:SS', description='Thời gian cập nhật')


class ResponseData(GenericModel, Generic[TypeX]):
    data: TypeX = Field(..., description='Dữ liệu trả về khi success')

    class Config:
        json_encoders = {
            datetime: lambda dt: datetime_to_str(dt)
        }


class FailResponse(BaseModel):
    error_code: str
    description: str
