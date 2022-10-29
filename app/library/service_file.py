import os
from typing import Dict, Optional, Tuple

import aiohttp
from dotenv import load_dotenv
from starlette import status

from app.library.constant.service_file import (
    SERVICE_FILE_API_FILES, SERVICE_FILE_HEADER
)

load_dotenv()


class ServiceFile:
    def __init__(self):
        self.session = None

    def start_session(self):
        self.session = aiohttp.ClientSession()

    async def close_session(self):
        await self.session.close()

    async def upload_file(self, file: bytes, temp_flag: bool = False) -> Tuple[bool, Optional[Dict[str, str]]]:
        try:
            async with self.session.post(
                    url=f'{os.getenv("SERVICE_FILE_URL")}/{SERVICE_FILE_API_FILES}',
                    headers=SERVICE_FILE_HEADER,
                    data={
                        'file': file,
                        'return_download_file_url_flag': "True",
                        'temp_flag': str(temp_flag)
                    }
            ) as response:
                if response.status == status.HTTP_201_CREATED:
                    is_success = True
                    response_data = await response.json()
                    output = {
                        'uuid': response_data['uuid'],
                        'file_url': response_data['file_url'],
                    }
                else:
                    is_success = False
                    output = {}

            return is_success, output
        except Exception:
            return False, None
