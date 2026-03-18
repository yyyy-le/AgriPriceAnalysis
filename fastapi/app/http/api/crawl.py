from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.http.deps import database_deps
from app.jobs.xinfadi_crawler import XinfadiCrawler

router = APIRouter(prefix='/crawl', tags=['爬虫管理'])

# 存储任务状态
crawl_status = {}


async def run_crawl_task(task_id: str, session: AsyncSession):
    try:
        crawl_status[task_id] = {"status": "running", "result": None}
        crawler = XinfadiCrawler(session)
        result = await crawler.run()
        crawl_status[task_id] = {"status": "success", "result": result}
    except Exception as e:
        crawl_status[task_id] = {"status": "failed", "result": str(e)}


@router.post('/xinfadi', name='触发新发地爬虫')
async def trigger_xinfadi(
    background_tasks: BackgroundTasks,
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
):
    import uuid
    task_id = str(uuid.uuid4())
    crawl_status[task_id] = {"status": "pending", "result": None}
    background_tasks.add_task(run_crawl_task, task_id, session)
    return {"task_id": task_id, "status": "started"}


@router.get('/status/{task_id}', name='查询爬虫状态')
async def get_crawl_status(task_id: str):
    status = crawl_status.get(task_id)
    if not status:
        return {"status": "not_found"}
    return {"task_id": task_id, **status}