from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter

import app.providers.rate_limiter_provider as rate_limiter_provider
from app.providers.database_provider import async_session_factory, redis_client
from app.jobs.alert_checker import start_alert_checker


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化限流器
    await FastAPILimiter.init(
        redis_client,
        identifier=rate_limiter_provider.default_identifier,
        http_callback=rate_limiter_provider.http_default_callback,
        ws_callback=rate_limiter_provider.ws_default_callback,
    )

    # 启动价格预警检查器后台任务
    alert_task = asyncio.create_task(start_alert_checker())

    # This hook ensures that a connection is opened to handle any queries
    yield
    # This hook ensures that the connection is closed when we've finished processing the request.

    # 取消价格预警检查器
    alert_task.cancel()
    try:
        await alert_task
    except asyncio.CancelledError:
        pass

    # 关闭限流器
    await FastAPILimiter.close()

    await async_session_factory().close_all()

    if redis_client:
        await redis_client.close()
