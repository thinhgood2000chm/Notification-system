import os

import aioredis
from dotenv import load_dotenv

load_dotenv()


async def redis_pool():
    redis = await aioredis.from_url(
        f"redis://{os.getenv('HOST_REDIS', 'localhost')}",
        username=f"{os.getenv('USERNAME_REDIS', '')}",
        password=f"{os.getenv('PASSWORD_REDIS', '')}",
        encoding="utf-8", decode_responses=True
    )
    return redis
