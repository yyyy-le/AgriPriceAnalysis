from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    source_name: str = ""
    source_url: str = ""

    @abstractmethod
    async def fetch(self, page: int, limit: int) -> dict:
        """抓取原始数据"""
        pass

    @abstractmethod
    async def parse(self, raw_data: dict) -> list[dict]:
        """解析为标准格式"""
        pass

    async def run(self) -> dict:
        """统一入口"""
        total_saved = 0
        total_skipped = 0
        limit = 10  # 每次请求10条
        # limit=100 #每次请求100条

        try:
            # 先抓第一页获取总数
            first = await self.fetch(page=1, limit=limit)
            total = first.get('count', 0)
            total_pages = min((total + limit - 1) // limit, 10)  # 最多10页
            logger.info(f"[{self.source_name}] 共 {total} 条数据，{total_pages} 页")
            #全部抓取
            # total_pages = (total + limit - 1) // limit
            # logger.info(f"[{self.source_name}] 共 {total} 条数据，{total_pages} 页")



            for page in range(1, total_pages + 1):
                logger.info(f"[{self.source_name}] 正在抓取第 {page}/{total_pages} 页")
                raw = await self.fetch(page=page, limit=limit)
                parsed = await self.parse(raw)
                saved, skipped = await self.save(parsed)
                total_saved += saved
                total_skipped += skipped

                # 如果这一页全部是重复数据，说明后面的也都有了，停止
                if saved == 0 and skipped > 0:
                    logger.info(f"[{self.source_name}] 检测到重复数据，停止抓取")
                    break

        except Exception as e:
            logger.error(f"[{self.source_name}] 爬虫异常: {e}")
            raise e

        return {
            "source": self.source_name,
            "total_saved": total_saved,
            "total_skipped": total_skipped
        }

    @abstractmethod
    async def save(self, data: list[dict]) -> tuple[int, int]:
        """保存数据，返回 (saved, skipped)"""
        pass