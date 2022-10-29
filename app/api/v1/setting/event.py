from typing import Callable

from fastapi import FastAPI
from loguru import logger

from app.library.service_file import ServiceFile

service_file = ServiceFile()
def create_start_app_handler(app: FastAPI) -> Callable:  # noqa
    async def startup_event():
        service_file.start_session()

    return startup_event


def create_stop_app_handler(app: FastAPI) -> Callable:  # noqa
    async def shutdown_event():
        await service_file.close_session()

    return shutdown_event
