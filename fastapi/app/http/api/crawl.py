from typing import Annotated
import uuid
import asyncio

from fastapi import APIRouter, BackgroundTasks, Body, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.http.deps import database_deps, auth_deps
from app.http.api.admin import require_admin, write_log
from app.jobs.xinfadi_crawler import XinfadiCrawler
from app.models.user import UserModel

router = APIRouter(prefix='/crawl', tags=['爬虫管理'])

crawl_status = {}
crawl_pause_events = {}
crawl_crawlers = {}  # 持有 crawler 引用，用于取消


async def run_crawl_task(task_id: str, session: AsyncSession, start_page: int = 1):
    pause_event = crawl_pause_events.get(task_id)
    try:
        crawl_status[task_id].update({
            "status": "running",
            "saved": 0,
            "skipped": 0,
            "page": 0,
            "total_pages": 0,
            "paused": False,
        })
        crawler = XinfadiCrawler(session)
        crawl_crawlers[task_id] = crawler

        async def on_progress(page, total_pages, saved, skipped):
            if pause_event:
                await pause_event.wait()
            crawl_status[task_id].update({
                "page": page,
                "total_pages": total_pages,
                "saved": saved,
                "skipped": skipped,
            })

        crawler.on_progress = on_progress
        result = await crawler.run(start_page=start_page)

        if result.get("cancelled"):
            crawl_status[task_id].update({
                "status": "cancelled",
                "result": result,
                "saved": result["total_saved"],
                "skipped": result["total_skipped"],
                "paused": False,
            })
        else:
            crawl_status[task_id].update({
                "status": "success",
                "result": result,
                "saved": result["total_saved"],
                "skipped": result["total_skipped"],
                "paused": False,
            })
    except Exception as e:
        crawl_status[task_id]["status"] = "failed"
        crawl_status[task_id]["result"] = str(e)
    finally:
        crawler = crawl_crawlers.pop(task_id, None)
        if crawler:
            await crawler.close()


@router.post('/xinfadi', name='触发新发地爬虫')
async def trigger_xinfadi(
    request: Request,
    background_tasks: BackgroundTasks,
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    admin: Annotated[UserModel, Depends(require_admin)],
    start_page: int = Body(1, embed=True),
):
    task_id = str(uuid.uuid4())
    pause_event = asyncio.Event()
    pause_event.set()
    crawl_pause_events[task_id] = pause_event
    crawl_status[task_id] = {
        "status": "pending",
        "result": None,
        "saved": 0,
        "skipped": 0,
        "page": 0,
        "total_pages": 0,
        "paused": False,
    }
    background_tasks.add_task(run_crawl_task, task_id, session, start_page)
    await write_log(session, admin, 'start_crawl', f'task_id:{task_id}', f'起始页:{start_page}', request)
    await session.commit()
    return {"task_id": task_id, "status": "started"}


@router.post('/pause/{task_id}', name='暂停爬虫')
async def pause_crawl(
    task_id: str,
    request: Request,
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    admin: Annotated[UserModel, Depends(require_admin)],
):
    event = crawl_pause_events.get(task_id)
    if event:
        event.clear()
        crawl_status[task_id]["paused"] = True
    await write_log(session, admin, 'pause_crawl', f'task_id:{task_id}', '', request)
    await session.commit()
    return {"success": True}


@router.post('/resume/{task_id}', name='继续爬虫')
async def resume_crawl(
    task_id: str,
    request: Request,
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    admin: Annotated[UserModel, Depends(require_admin)],
):
    event = crawl_pause_events.get(task_id)
    if event:
        event.set()
        crawl_status[task_id]["paused"] = False
    await write_log(session, admin, 'resume_crawl', f'task_id:{task_id}', '', request)
    await session.commit()
    return {"success": True}


@router.post('/cancel/{task_id}', name='取消爬虫')
async def cancel_crawl(
    task_id: str,
    request: Request,
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    admin: Annotated[UserModel, Depends(require_admin)],
):
    event = crawl_pause_events.get(task_id)
    if event:
        event.set()
    crawler = crawl_crawlers.get(task_id)
    if crawler:
        crawler.cancel()
    if task_id in crawl_status:
        crawl_status[task_id]["paused"] = False
    await write_log(session, admin, 'cancel_crawl', f'task_id:{task_id}', '', request)
    await session.commit()
    return {"success": True}


@router.get('/status/{task_id}', name='查询爬虫状态')
async def get_crawl_status(task_id: str):
    status = crawl_status.get(task_id)
    if not status:
        return {"status": "not_found"}
    return {"task_id": task_id, **status}