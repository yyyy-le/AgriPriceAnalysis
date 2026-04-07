import asyncio
import aiohttp
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.jobs.base_crawler import BaseCrawler
import logging

logger = logging.getLogger(__name__)

XINFADI_URL = "http://www.xinfadi.com.cn/getPriceData.html"


class XinfadiCrawler(BaseCrawler):
    source_name = "新发地"
    source_url = XINFADI_URL

    def __init__(self, session: AsyncSession):
        self.session = session

    async def fetch(self, page: int = 1, limit: int = 100) -> dict:
        params = {
            "limit": limit,
            "current": page,
            "pubDateStartTime": "",
            "pubDateEndTime": "",
            "prodCatid": "",
            "prodName": ""
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "http://www.xinfadi.com.cn/priceDetail.html"
        }
        async with aiohttp.ClientSession() as client:
            async with client.get(XINFADI_URL, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                return await resp.json(content_type=None)

    async def parse(self, raw_data: dict) -> list[dict]:
        items = raw_data.get("list", [])
        result = []
        for item in items:
            result.append({
                "prod_name": item.get("prodName", "").strip(),
                "prod_cat": item.get("prodCat", "").strip(),
                "prod_catid": item.get("prodCatid"),
                "low_price": float(item.get("lowPrice") or 0),
                "high_price": float(item.get("highPrice") or 0),
                "avg_price": float(item.get("avgPrice") or 0),
                "place": item.get("place", "").strip(),
                "spec_info": item.get("specInfo", "").strip(),
                "unit_info": item.get("unitInfo", "").strip(),
                "pub_date": item.get("pubDate", ""),
            })
        return result

    async def save(self, data: list[dict]) -> tuple[int, int]:
        saved = 0
        skipped = 0

        for item in data:
            try:
                # 1. 获取或创建分类
                category_id = await self._get_or_create_category(item["prod_cat"], item["prod_catid"])

                # 2. 获取或创建产品
                product_id = await self._get_or_create_product(
                    item["prod_name"], category_id, item["unit_info"], item["spec_info"]
                )

                # 3. 获取或创建市场（产地）
                market_id = await self._get_or_create_market(item["place"])

                # 4. 插入价格记录（重复跳过）
                pub_date = datetime.strptime(item["pub_date"], "%Y-%m-%d %H:%M:%S")
                result = await self.session.execute(text("""
                    INSERT INTO price_records (time, product_id, market_id, price, min_price, max_price, avg_price, source, spec_info, unit_info)
                    VALUES (:time, :product_id, :market_id, :price, :min_price, :max_price, :avg_price, :source, :spec_info, :unit_info)
                    ON CONFLICT DO NOTHING
                    RETURNING time
                """), {
                    "time": pub_date,
                    "product_id": product_id,
                    "market_id": market_id,
                    "price": item["avg_price"],
                    "min_price": item["low_price"],
                    "max_price": item["high_price"],
                    "avg_price": item["avg_price"],
                    "source": "xinfadi",
                    "spec_info": item["spec_info"],
                    "unit_info": item["unit_info"]
                })

                if result.fetchone():
                    saved += 1
                else:
                    skipped += 1

            except Exception as e:
                logger.error(f"保存数据失败: {item}, 错误: {e}")
                skipped += 1

        await self.session.commit()
        return saved, skipped

    async def _get_or_create_category(self, name: str, catid: int) -> int:
        result = await self.session.execute(
            text("SELECT id FROM categories WHERE id = :id"), {"id": catid}
        )
        row = result.fetchone()
        if row:
            return row[0]

        await self.session.execute(
            text("INSERT INTO categories (id, name) VALUES (:id, :name) ON CONFLICT DO NOTHING"),
            {"id": catid, "name": name}
        )
        return catid

    async def _get_or_create_product(self, name: str, category_id: int, unit: str, remark: str) -> int:
        result = await self.session.execute(
            text("SELECT id FROM products WHERE name = :name AND category_id = :cat_id"),
            {"name": name, "cat_id": category_id}
        )
        row = result.fetchone()
        if row:
            return row[0]

        result = await self.session.execute(
            text("""
                INSERT INTO products (name, category_id, unit, remark)
                VALUES (:name, :category_id, :unit, :remark)
                RETURNING id
            """),
            {"name": name, "category_id": category_id, "unit": unit, "remark": remark}
        )
        return result.fetchone()[0]

    async def _get_or_create_market(self, place: str) -> int:
        if not place:
            place = "未知"

        result = await self.session.execute(
            text("SELECT id FROM markets WHERE name = :name"), {"name": place}
        )
        row = result.fetchone()
        if row:
            return row[0]

        result = await self.session.execute(
            text("INSERT INTO markets (name) VALUES (:name) RETURNING id"),
            {"name": place}
        )
        return result.fetchone()[0]