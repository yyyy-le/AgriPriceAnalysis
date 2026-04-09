from typing import Annotated, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile

from app.http.deps import database_deps, auth_deps
from app.models.user import UserModel

router = APIRouter(prefix='/admin', tags=['管理员'])


def require_admin(user: UserModel = Depends(auth_deps.get_auth_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail='无权限')
    return user


# ===== 用户管理 =====

@router.get('/users', name='用户列表')
async def get_users(
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    admin: Annotated[UserModel, Depends(require_admin)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None),
):
    offset = (page - 1) * page_size
    params = {"limit": page_size, "offset": offset}
    where_clauses = ["1=1"]

    if keyword:
        where_clauses.append("(username ILIKE :keyword OR cellphone ILIKE :keyword)")
        params["keyword"] = f"%{keyword}%"

    where = " AND ".join(where_clauses)

    sql = f"""
        SELECT id, username, cellphone, state, is_admin, created_at
        FROM users
        WHERE {where}
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
    """
    count_sql = f"SELECT COUNT(*) FROM users WHERE {where}"

    rows = await session.execute(text(sql), params)
    count_params = {k: v for k, v in params.items() if k not in ('limit', 'offset')}
    total = await session.execute(text(count_sql), count_params)

    return {
        "total": total.scalar(),
        "page": page,
        "page_size": page_size,
        "list": [dict(r._mapping) for r in rows],
    }


@router.post('/users', name='新增用户')
async def create_user_by_admin(
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    admin: Annotated[UserModel, Depends(require_admin)],
    username: str = Body(...),
    cellphone: str = Body(...),
    password: str = Body(...),
    is_admin: bool = Body(False),
    enabled: bool = Body(True),
):
    from app.support.password_helper import get_password_hash

    exists = await session.execute(
        text("SELECT id FROM users WHERE username = :username"),
        {"username": username}
    )
    if exists.fetchone():
        raise HTTPException(status_code=400, detail=f'用户名「{username}」已存在')

    exists_phone = await session.execute(
        text("SELECT id FROM users WHERE cellphone = :cellphone"),
        {"cellphone": cellphone}
    )
    if exists_phone.fetchone():
        raise HTTPException(status_code=400, detail=f'手机号「{cellphone}」已被注册')

    hashed = get_password_hash(password)
    state = 'enabled' if enabled else 'disabled'
    await session.execute(text("""
        INSERT INTO users (id, username, password, cellphone, state, is_admin)
        VALUES (gen_random_uuid(), :username, :password, :cellphone, :state, :is_admin)
    """), {
        "username": username, "password": hashed,
        "cellphone": cellphone, "state": state, "is_admin": is_admin
    })
    await session.commit()
    return {"success": True}


@router.put('/users/{user_id}', name='编辑用户')
async def update_user_by_admin(
    user_id: str,
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    admin: Annotated[UserModel, Depends(require_admin)],
    cellphone: str = Body(...),
    password: str = Body(''),
    is_admin: bool = Body(False),
    enabled: bool = Body(True),
):
    from app.support.password_helper import get_password_hash

    exists_phone = await session.execute(
        text("SELECT id FROM users WHERE cellphone = :cellphone AND id != :id"),
        {"cellphone": cellphone, "id": user_id}
    )
    if exists_phone.fetchone():
        raise HTTPException(status_code=400, detail=f'手机号「{cellphone}」已被其他用户注册')

    state = 'enabled' if enabled else 'disabled'

    if password:
        await session.execute(text("""
            UPDATE users SET cellphone=:cellphone, password=:password,
            is_admin=:is_admin, state=:state WHERE id=:id
        """), {
            "cellphone": cellphone,
            "password": get_password_hash(password),
            "is_admin": is_admin, "state": state, "id": user_id
        })
    else:
        await session.execute(text("""
            UPDATE users SET cellphone=:cellphone,
            is_admin=:is_admin, state=:state WHERE id=:id
        """), {
            "cellphone": cellphone,
            "is_admin": is_admin, "state": state, "id": user_id
        })

    await session.commit()
    return {"success": True}


@router.patch('/users/{user_id}/state', name='修改用户状态')
async def update_user_state(
    user_id: str,
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    admin: Annotated[UserModel, Depends(require_admin)],
    state: str = Query(..., pattern='^(enabled|disabled)$'),
):
    await session.execute(
        text("UPDATE users SET state = :state WHERE id = :id"),
        {"state": state, "id": user_id}
    )
    await session.commit()
    return {"success": True}


@router.patch('/users/{user_id}/admin', name='设置管理员')
async def update_user_admin(
    user_id: str,
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    admin: Annotated[UserModel, Depends(require_admin)],
    is_admin: bool = Query(...),
):
    await session.execute(
        text("UPDATE users SET is_admin = :is_admin WHERE id = :id"),
        {"is_admin": is_admin, "id": user_id}
    )
    await session.commit()
    return {"success": True}


@router.delete('/users/{user_id}', name='删除用户')
async def delete_user(
    user_id: str,
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    admin: Annotated[UserModel, Depends(require_admin)],
):
    await session.execute(
        text("UPDATE users SET deleted_at = NOW() WHERE id = :id"),
        {"id": user_id}
    )
    await session.commit()
    return {"success": True}


# ===== 数据管理：按产品聚合 =====

@router.get('/data/products', name='按产品聚合价格数据')
async def get_products_aggregated(
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    admin: Annotated[UserModel, Depends(require_admin)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    product_name: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    parent_category_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
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
    elif parent_category_id:
        where_clauses.append("c.parent_id = :parent_category_id")
        params["parent_category_id"] = parent_category_id
    # 日期条件：直接拼字符串到 SQL，避免 asyncpg 参数解析问题
    lateral_date_clauses = ["product_id = p.id"]
    if start_date:
        lateral_date_clauses.append(f"time >= '{start_date}'")
    if end_date:
        lateral_date_clauses.append(f"time < '{end_date}'::date + INTERVAL '1 day'")

    lateral_where = " AND ".join(lateral_date_clauses)
    outer_where = " AND ".join(where_clauses)  # 只含 p.name / p.category_id

    sql = f"""
        SELECT
            p.id as product_id,
            p.name as product_name,
            CASE WHEN c.parent_id IS NULL THEN c.name ELSE pc.name END as parent_category_name,
            CASE WHEN c.parent_id IS NULL THEN NULL ELSE c.name END as category_name,
            p.unit,
            stats.record_count,
            stats.min_price,
            stats.max_price,
            stats.latest_avg,
            stats.latest_date,
            stats.source
        FROM products p
        JOIN categories c ON p.category_id = c.id
        LEFT JOIN categories pc ON c.parent_id = pc.id
        JOIN LATERAL (
            SELECT
                COUNT(*) as record_count,
                ROUND(MIN(min_price)::numeric, 2) as min_price,
                ROUND(MAX(max_price)::numeric, 2) as max_price,
                ROUND(AVG(avg_price)::numeric, 2) as latest_avg,
                DATE(MAX(time)) as latest_date,
                MAX(source) as source
            FROM price_records
            WHERE {lateral_where}
        ) stats ON stats.record_count > 0
        WHERE {outer_where}
        ORDER BY stats.latest_date DESC, p.name ASC
        LIMIT :limit OFFSET :offset
    """

    count_sql = f"""
        SELECT COUNT(DISTINCT p.id)
        FROM products p
        JOIN categories c ON p.category_id = c.id
        JOIN LATERAL (
            SELECT COUNT(*) as cnt
            FROM price_records
            WHERE {lateral_where}
        ) stats ON stats.cnt > 0
        WHERE {outer_where}
    """

    total_records_sql = f"""
        SELECT COUNT(*)
        FROM price_records pr
        JOIN products p ON pr.product_id = p.id
        JOIN categories c ON p.category_id = c.id
        WHERE pr.product_id = p.id
        {f"AND pr.time >= '{start_date}'" if start_date else ""}
        {f"AND pr.time < '{end_date}'::date + INTERVAL '1 day'" if end_date else ""}
        {f"AND p.name ILIKE :product_name" if product_name else ""}
        {f"AND p.category_id = :category_id" if category_id else ""}
    """

    rows = await session.execute(text(sql), params)
    count_params = {k: v for k, v in params.items() if k not in ('limit', 'offset')}
    total = await session.execute(text(count_sql), count_params)
    total_records = await session.execute(text(total_records_sql), count_params)

    return {
        "total": total.scalar(),
        "total_records": total_records.scalar(),
        "page": page,
        "page_size": page_size,
        "list": [dict(r._mapping) for r in rows],
    }


# ===== 数据管理：原始记录（用于展开行） =====

@router.get('/data/records', name='价格记录列表')
async def get_price_records(
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    admin: Annotated[UserModel, Depends(require_admin)],
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    product_id: Optional[int] = Query(None),
    product_name: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    if product_id:
        # 日期条件直接拼字符串，避免 asyncpg 参数解析问题
        date_clause = ""
        if start_date:
            date_clause += f" AND pr.time >= '{start_date}'"
        if end_date:
            date_clause += f" AND pr.time < '{end_date}'::date + INTERVAL '1 day'"
        # 没有指定日期范围时，默认取最近 90 天
        if not start_date and not end_date:
            date_clause = """ AND pr.time >= (
                  SELECT MAX(time) - INTERVAL '90 days'
                  FROM price_records
                  WHERE product_id = :product_id
              )"""

        sql = f"""
            SELECT
                pr.time, pr.product_id, pr.min_price, pr.max_price,
                pr.avg_price, pr.source, pr.spec_info, pr.unit_info, m.name as market_name
            FROM price_records pr
            LEFT JOIN markets m ON pr.market_id = m.id
            WHERE pr.product_id = :product_id
            {date_clause}
            ORDER BY pr.time DESC
            LIMIT :limit
        """
        rows = await session.execute(text(sql), {"product_id": product_id, "limit": page_size})
        return {
            "total": page_size,
            "page": 1,
            "page_size": page_size,
            "list": [dict(r._mapping) for r in rows],
        }

    # 通用场景：按产品名模糊搜索（带完整 JOIN）
    offset = (page - 1) * page_size
    params = {"limit": page_size, "offset": offset}
    where_clauses = ["1=1"]
    if product_name:
        where_clauses.append("p.name ILIKE :product_name")
        params["product_name"] = f"%{product_name}%"
    where = " AND ".join(where_clauses)

    sql = f"""
        SELECT pr.time, pr.product_id, p.name as product_name,
               c.name as category_name, m.name as market_name,
               pr.min_price, pr.max_price, pr.avg_price, pr.spec_info, pr.unit_info, pr.source
        FROM price_records pr
        JOIN products p ON pr.product_id = p.id
        JOIN categories c ON p.category_id = c.id
        LEFT JOIN markets m ON pr.market_id = m.id
        WHERE {where}
        ORDER BY pr.time DESC
        LIMIT :limit OFFSET :offset
    """
    count_sql = f"""
        SELECT COUNT(*) FROM price_records pr
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


@router.delete('/data/records', name='删除价格记录')
async def delete_price_record(
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    admin: Annotated[UserModel, Depends(require_admin)],
    product_id: int = Query(...),
    time: str = Query(...),
):
    from dateutil import parser as dateparser
    parsed_time = dateparser.parse(time)
    await session.execute(
        text("DELETE FROM price_records WHERE product_id = :product_id AND time = :time"),
        {"product_id": product_id, "time": parsed_time}
    )
    await session.commit()
    return {"success": True}


@router.put('/data/records', name='编辑价格记录')
async def update_price_record(
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    admin: Annotated[UserModel, Depends(require_admin)],
    product_id: int = Body(...),
    time: str = Body(...),
    avg_price: float = Body(...),
    min_price: float = Body(...),
    max_price: float = Body(...),
):
    from dateutil import parser as dateparser
    parsed_time = dateparser.parse(time)
    await session.execute(text("""
        UPDATE price_records
        SET avg_price = :avg_price, min_price = :min_price, max_price = :max_price
        WHERE product_id = :product_id AND time = :time
    """), {
        "avg_price": avg_price, "min_price": min_price,
        "max_price": max_price, "product_id": product_id, "time": parsed_time
    })
    await session.commit()
    return {"success": True}


@router.post('/data/import-csv', name='CSV导入价格数据')
async def import_csv(
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    admin: Annotated[UserModel, Depends(require_admin)],
    file: UploadFile = File(...),
):
    import csv
    import io

    content = await file.read()
    text_content = content.decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(text_content))

    saved = 0
    skipped = 0
    errors = []

    for i, row in enumerate(reader, start=2):
        try:
            product_name = row.get('产品名称', '').strip()
            parent_cat_name = row.get('一级分类', '').strip()
            category_name = row.get('二级分类', '').strip()
            market_name = row.get('市场/产地', '').strip() or '未知'
            avg_price = float(row.get('均价', 0))
            min_price = float(row.get('最低价', 0))
            max_price = float(row.get('最高价', 0))
            unit = row.get('单位', '').strip()
            date_str = row.get('日期', '').strip()

            if not product_name or not date_str:
                errors.append(f'第{i}行：产品名称或日期为空')
                skipped += 1
                continue

            from dateutil import parser as dateparser
            record_time = dateparser.parse(date_str)
            if not record_time:
                errors.append(f'第{i}行：日期格式无法识别「{date_str}」')
                skipped += 1
                continue
            record_time = record_time.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)

            # 处理一级分类
            parent_cat_id = None
            if parent_cat_name:
                pc_row = await session.execute(
                    text("SELECT id FROM categories WHERE name = :name AND parent_id IS NULL"),
                    {"name": parent_cat_name}
                )
                pc = pc_row.fetchone()
                if pc:
                    parent_cat_id = pc[0]
                else:
                    pc_result = await session.execute(
                        text("INSERT INTO categories (name) VALUES (:name) RETURNING id"),
                        {"name": parent_cat_name}
                    )
                    parent_cat_id = pc_result.fetchone()[0]

            # 处理二级分类（挂在一级下），若无二级则用一级作为产品分类
            if category_name:
                c_row = await session.execute(
                    text("SELECT id FROM categories WHERE name = :name AND parent_id IS NOT DISTINCT FROM :parent_id"),
                    {"name": category_name, "parent_id": parent_cat_id}
                )
                c = c_row.fetchone()
                if c:
                    category_id = c[0]
                else:
                    c_result = await session.execute(
                        text("INSERT INTO categories (name, parent_id) VALUES (:name, :parent_id) RETURNING id"),
                        {"name": category_name, "parent_id": parent_cat_id}
                    )
                    category_id = c_result.fetchone()[0]
            elif parent_cat_id:
                category_id = parent_cat_id
            else:
                errors.append(f'第{i}行：一级分类和二级分类均为空')
                skipped += 1
                continue

            prod_row = await session.execute(
                text("SELECT id FROM products WHERE name = :name AND category_id = :cat_id"),
                {"name": product_name, "cat_id": category_id}
            )
            prod = prod_row.fetchone()
            if prod:
                product_id = prod[0]
            else:
                prod_result = await session.execute(
                    text("INSERT INTO products (name, category_id, unit, remark) VALUES (:name, :cat_id, :unit, '') RETURNING id"),
                    {"name": product_name, "cat_id": category_id, "unit": unit}
                )
                product_id = prod_result.fetchone()[0]

            mkt_row = await session.execute(
                text("SELECT id FROM markets WHERE name = :name"), {"name": market_name}
            )
            mkt = mkt_row.fetchone()
            if mkt:
                market_id = mkt[0]
            else:
                mkt_result = await session.execute(
                    text("INSERT INTO markets (name) VALUES (:name) RETURNING id"),
                    {"name": market_name}
                )
                market_id = mkt_result.fetchone()[0]

            ins = await session.execute(text("""
                INSERT INTO price_records (time, product_id, market_id, price, min_price, max_price, avg_price, source)
                VALUES (:time, :product_id, :market_id, :avg_price, :min_price, :max_price, :avg_price, 'csv')
                ON CONFLICT DO NOTHING
                RETURNING time
            """), {
                "time": record_time, "product_id": product_id, "market_id": market_id,
                "avg_price": avg_price, "min_price": min_price, "max_price": max_price
            })

            if ins.fetchone():
                saved += 1
            else:
                skipped += 1

        except Exception as e:
            errors.append(f'第{i}行处理失败：{str(e)}')
            skipped += 1

    await session.commit()
    return {"saved": saved, "skipped": skipped, "errors": errors}


# ===== 系统日志 =====

@router.get('/logs', name='系统日志')
async def get_logs(
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    admin: Annotated[UserModel, Depends(require_admin)],
):
    sql = """
        SELECT source, MAX(time) as last_run, COUNT(*) as total_records
        FROM price_records
        GROUP BY source
        ORDER BY last_run DESC
    """
    rows = await session.execute(text(sql))
    return [dict(r._mapping) for r in rows]