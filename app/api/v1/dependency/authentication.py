import os
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv
from fastapi import Header, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from starlette.status import HTTP_403_FORBIDDEN

from app.api.v1.setting.function import http_exception
from app.library.constant.server_auth import SERVER_AUTH_TYPE
from app.library.constant.system_type import SYSTEM_TYPE
from app.model.base import db

load_dotenv()

EXPIRES_TIME = 300


async def get_system(
        server_auth: Optional[str] = Header(None)
):
    if server_auth is None:
        return http_exception(status_code=HTTP_403_FORBIDDEN, description="server-auth not found")
    if server_auth not in SERVER_AUTH_TYPE:
        return http_exception(status_code=HTTP_403_FORBIDDEN, description="Incorrect token")
    return SYSTEM_TYPE[SERVER_AUTH_TYPE[server_auth]]


async def create_access_token(watcher_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=EXPIRES_TIME)
    encode_data = {"exp": expire, "sub": str(watcher_id)}
    encoded_jwt = jwt.encode(encode_data, os.getenv('JWT_SECRET_KEY'), algorithm=os.getenv("ALGORITHM"))
    return encoded_jwt


async def get_current_user(
        scheme_and_credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())
):
    try:
        payload = jwt.decode(
            scheme_and_credentials.credentials, os.getenv('JWT_SECRET_KEY'), algorithms=[os.getenv("ALGORITHM")]
        )
        watcher_id: str = payload.get("sub")
        if watcher_id is None:
            return http_exception(status_code=HTTP_403_FORBIDDEN, description="token is not valid")
        watcher = await db.watcher.find_one({"watcher_id": watcher_id})
        return watcher
    except JWTError:
        raise http_exception(status_code=HTTP_403_FORBIDDEN, description="token is not valid")
