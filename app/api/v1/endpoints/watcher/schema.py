from bson import ObjectId
from pydantic import BaseModel, Field

from app.model.base import Base, PyObjectId


class WatcherSchema(BaseModel):
    watcher_id: str = Field(...)
    avatar_url: str = Field(...)
    username: str = Field(...)


class WatcherResponseSchema(Base):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    watcher_id: str = Field(...)
    avatar_url: str = Field(...)
    username: str = Field(...)

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}


class DeleteWacherRequest(BaseModel):
    list_watcher_id: list = Field(...)


class UserTokenResponse(BaseModel):
    watcher_id: str = Field(...)
    token: str = Field(...)


class WatcherIdRequest(BaseModel):
    watcher_id: str = Field(...)
