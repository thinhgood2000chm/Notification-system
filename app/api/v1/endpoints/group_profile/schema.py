from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field

from app.model.base import Base, PyObjectId


class GroupProfileRequest(BaseModel):
    group_profile_id: str = Field(...)
    watcher_ids: Optional[list]


class GroupProfileResponse(Base):
    id: PyObjectId = Field(..., alias="_id")
    group_profile_id: str = Field(...)
    watcher_ids: list = Field(...)
    activity_ids: list = Field(...)

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}


class UpdateWatcherGroupProfileRequest(BaseModel):
    watcher_ids: list = Field(...)
