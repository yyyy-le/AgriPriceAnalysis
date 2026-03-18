from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.http.deps import database_deps, auth_deps
from app.models.user import UserModel

router = APIRouter(prefix='/prices', tags=['价格数据'])


@router.get('/summary', name='数据概览统计')
async def get_summary(
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    user: Annotated[UserModel, Depends(auth_deps.get_auth_user)],
):
    total = (await session.execute(text("SELECT COUNT(*) FROM price_records"))).scalar() or 0
    products = (await session.execute(text("SELECT COUNT(*) FROM products"))).scalar() or 0
    categories = (await session.execute(text("SELECT COUNT(*) FROM categories"))).scalar() or 0
    markets = (await session.execute(text("SELECT COUNT(*) FROM markets"))).scalar() or 0
    latest = (await session.execute(text("SELECT MAX(time) FROM price_records"))).scalar()
    return {
        "total_records": int(total),
        "total_products": int(products),
        "total_categories": int(categories),
        "total_markets": int(markets),
        "latest_update": str(latest) if latest else None,
    }


@router.get('/daily-avg', name='近30天每日全品类均价')
async def get_daily_avg(
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    user: Annotated[UserModel, Depends(auth_deps.get_auth_user)],
):
    sql = """
        SELECT DATE(time) as date, ROUND(AVG(avg_price)::numeric, 2) as avg_price
        FROM price_records
        GROUP BY DATE(time)
        ORDER BY date DESC
        LIMIT 30
    """
    rows = await session.execute(text(sql))
    result = [dict(r._mapping) for r in rows]
    result.reverse()
    return result


@router.get('/category-stats', name='各分类记录数占比')
async def get_category_stats(
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    user: Annotated[UserModel, Depends(auth_deps.get_auth_user)],
):
    sql = """
        SELECT c.name as category_name, COUNT(*) as count
        FROM price_records pr
        JOIN products p ON pr.product_id = p.id
        JOIN categories c ON p.category_id = c.id
        GROUP BY c.name
        ORDER BY count DESC
    """
    rows = await session.execute(text(sql))
    return [dict(r._mapping) for r in rows]


@router.get('/top-expensive', name='今日最贵产品Top10')
async def get_top_expensive(
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    user: Annotated[UserModel, Depends(auth_deps.get_auth_user)],
):
    sql = """
        SELECT p.name as product_name, ROUND(AVG(pr.avg_price)::numeric, 2) as avg_price, p.unit
        FROM price_records pr
        JOIN products p ON pr.product_id = p.id
        WHERE DATE(pr.time) = (SELECT DATE(MAX(time)) FROM price_records)
        GROUP BY p.name, p.unit
        ORDER BY avg_price DESC
        LIMIT 10
    """
    rows = await session.execute(text(sql))
    return [dict(r._mapping) for r in rows]


@router.get('/top-cheapest', name='今日最便宜产品Top10')
async def get_top_cheapest(
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    user: Annotated[UserModel, Depends(auth_deps.get_auth_user)],
):
    sql = """
        SELECT p.name as product_name, ROUND(AVG(pr.avg_price)::numeric, 2) as avg_price, p.unit
        FROM price_records pr
        JOIN products p ON pr.product_id = p.id
        WHERE DATE(pr.time) = (SELECT DATE(MAX(time)) FROM price_records)
        GROUP BY p.name, p.unit
        ORDER BY avg_price ASC
        LIMIT 10
    """
    rows = await session.execute(text(sql))
    return [dict(r._mapping) for r in rows]


@router.get('/price-volatility', name='价格波动最大Top8')
async def get_price_volatility(
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    user: Annotated[UserModel, Depends(auth_deps.get_auth_user)],
):
    sql = """
        SELECT p.name as product_name,
               ROUND(((MAX(pr.max_price) - MIN(pr.min_price)) / NULLIF(AVG(pr.avg_price), 0) * 100)::numeric, 1) as volatility
        FROM price_records pr
        JOIN products p ON pr.product_id = p.id
        GROUP BY p.name
        HAVING AVG(pr.avg_price) > 0
        ORDER BY volatility DESC
        LIMIT 8
    """
    rows = await session.execute(text(sql))
    return [dict(r._mapping) for r in rows]


@router.get('/market-stats', name='各市场数据量')
async def get_market_stats(
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    user: Annotated[UserModel, Depends(auth_deps.get_auth_user)],
):
    sql = """
        SELECT m.name as market_name, COUNT(*) as count
        FROM price_records pr
        LEFT JOIN markets m ON pr.market_id = m.id
        GROUP BY m.name
        ORDER BY count DESC
        LIMIT 10
    """
    rows = await session.execute(text(sql))
    return [dict(r._mapping) for r in rows]


@router.get('/list', name='价格列表')
async def get_price_list(
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    user: Annotated[UserModel, Depends(auth_deps.get_auth_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    product_name: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
):
    offset = (page - 1) * page_size
    params = {"limit": page_size, "offset": offset}
    where_clauses = ["1=1"]

    if product_name:
        where_clauses.append("p.name ILIKE :product_name")
        params["product_name"] = f"%{product_name}%"
    if category_id:
        where_clauses.append("p.category_id = :category_id")
        params["category_id"] = category_id

    where = " AND ".join(where_clauses)

    sql = f"""
        SELECT pr.time, p.name as product_name, c.name as category_name,
               m.name as market_name, pr.min_price, pr.max_price, pr.avg_price, p.unit
        FROM price_records pr
        JOIN products p ON pr.product_id = p.id
        JOIN categories c ON p.category_id = c.id
        LEFT JOIN markets m ON pr.market_id = m.id
        WHERE {where}
        ORDER BY pr.time DESC
        LIMIT :limit OFFSET :offset
    """
    count_sql = f"""
        SELECT COUNT(*)
        FROM price_records pr
        JOIN products p ON pr.product_id = p.id
        WHERE {where}
    """

    rows = await session.execute(text(sql), params)
    count_params = {k: v for k, v in params.items() if k not in ('limit', 'offset')}
    total = await session.execute(text(count_sql), count_params)

    return {
        "total": total.scalar(),
        "page": page,
        "page_size": page_size,
        "list": [dict(r._mapping) for r in rows],
    }


@router.get('/categories', name='分类列表')
async def get_categories(
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    user: Annotated[UserModel, Depends(auth_deps.get_auth_user)],
):
    rows = await session.execute(text("SELECT id, name FROM categories ORDER BY id"))
    return [dict(r._mapping) for r in rows]


@router.get('/trend', name='价格趋势')
async def get_price_trend(
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    user: Annotated[UserModel, Depends(auth_deps.get_auth_user)],
    product_id: int = Query(...),
    days: int = Query(30, ge=7, le=365),
):
    sql = f"""
        SELECT DATE(pr.time) as date, AVG(pr.avg_price) as avg_price,
               MIN(pr.min_price) as min_price, MAX(pr.max_price) as max_price
        FROM price_records pr
        WHERE pr.product_id = :product_id
          AND pr.time >= NOW() - INTERVAL '{days} days'
        GROUP BY DATE(pr.time)
        ORDER BY date ASC
    """
    rows = await session.execute(text(sql), {"product_id": product_id})
    return [dict(r._mapping) for r in rows]


@router.get('/top-products', name='热门产品价格')
async def get_top_products(
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    user: Annotated[UserModel, Depends(auth_deps.get_auth_user)],
):
    sql = """
        SELECT DISTINCT ON (p.id)
               p.id, p.name as product_name, p.unit, c.name as category_name,
               pr.avg_price, pr.min_price, pr.max_price, pr.time
        FROM price_records pr
        JOIN products p ON pr.product_id = p.id
        JOIN categories c ON p.category_id = c.id
        ORDER BY p.id, pr.time DESC
        LIMIT 20
    """
    rows = await session.execute(text(sql))
    return [dict(r._mapping) for r in rows]

@router.get('/products/search', name='搜索产品')
async def search_products(
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    user: Annotated[UserModel, Depends(auth_deps.get_auth_user)],
    keyword: str = Query('', description='产品名称关键词'),
):
    sql = """
        SELECT p.id, p.name as product_name, p.unit, c.name as category_name
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.name ILIKE :keyword
        ORDER BY p.name
        LIMIT 50
    """
    rows = await session.execute(text(sql), {"keyword": f"%{keyword}%"})
    return [dict(r._mapping) for r in rows]