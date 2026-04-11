from abc import ABC, abstractmethod
import asyncio
import random
import logging

logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    source_name: str = ""
    source_url: str = ""
    on_progress = None   # 进度回调，签名: async (page, total_pages, saved, skipped)
    _cancelled = False   # 取消标志

    @abstractmethod
    async def fetch(self, page: int, limit: int) -> dict:
        pass

    @abstractmethod
    async def parse(self, raw_data: dict) -> list[dict]:
        pass

    async def run(self, start_page: int = 1) -> dict:
        total_saved = 0
        total_skipped = 0
        self._cancelled = False
        limit = 100

        try:
            # first = await self.fetch(page=start_page, limit=limit)
            # total = first.get('count', 0)
            # total_pages = (total + limit - 1) // limit
            # logger.info(f"[{self.source_name}] 共 {total} 条数据，{total_pages} 页")
            total_pages = 2600  # 手动设置总页数，按需调整
            logger.info(f"[{self.source_name}] 从第 {start_page} 页开始，共 {total_pages} 页")

            for page in range(start_page, total_pages + 1):
                if self._cancelled:
                    logger.info(f"[{self.source_name}] 任务已取消")
                    break

                logger.info(f"[{self.source_name}] 正在抓取第 {page}/{total_pages} 页")
                raw = await self.fetch(page=page, limit=limit)
                parsed = await self.parse(raw)
                saved, skipped = await self.save(parsed)
                total_saved += saved
                total_skipped += skipped

                if self.on_progress:
                    await self.on_progress(page, total_pages, total_saved, total_skipped)

                if page < total_pages:
                    await asyncio.sleep(random.uniform(1, 1.5))

                # TODO: 重复检测暂时关闭，待完善检测逻辑后重新启用
                # if saved == 0 and skipped > 0:
                #     logger.info(f"[{self.source_name}] 检测到重复数据，停止抓取")
                #     break

        except Exception as e:
            logger.error(f"[{self.source_name}] 爬虫异常: {e}")
            raise e

        return {
            "source": self.source_name,
            "total_saved": total_saved,
            "total_skipped": total_skipped,
            "cancelled": self._cancelled,
        }

    def cancel(self):
        self._cancelled = True

    @abstractmethod
    async def save(self, data: list[dict]) -> tuple[int, int]:
        pass