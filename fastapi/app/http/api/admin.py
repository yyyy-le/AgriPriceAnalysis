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
        where_clauses.append("(username ILIKE :keyword OR cellphone ILIKE :keyword OR nickname ILIKE :keyword)")
        params["keyword"] = f"%{keyword}%"

    where = " AND ".join(where_clauses)

    sql = f"""
        SELECT id, username, nickname, cellphone, state, gender, is_admin, created_at
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
    nickname: str = Body(...),
    cellphone: str = Body(...),
    password: str = Body(...),
    gender: str = Body('unknown'),
    is_admin: bool = Body(False),
    enabled: bool = Body(True),
):
    from app.support.password_helper import get_password_hash

    # 检查用户名是否重复
    exists = await session.execute(
        text("SELECT id FROM users WHERE username = :username"),
        {"username": username}
    )
    if exists.fetchone():
        raise HTTPException(status_code=400, detail=f'用户名「{username}」已存在')

    # 检查手机号是否重复
    exists_phone = await session.execute(
        text("SELECT id FROM users WHERE cellphone = :cellphone"),
        {"cellphone": cellphone}
    )
    if exists_phone.fetchone():
        raise HTTPException(status_code=400, detail=f'手机号「{cellphone}」已被注册')

    hashed = get_password_hash(password)
    state = 'enabled' if enabled else 'disabled'
    await session.execute(text("""
        INSERT INTO users (id, username, nickname, password, cellphone, state, gender, avatar, is_admin)
        VALUES (gen_random_uuid(), :username, :nickname, :password, :cellphone, :state, :gender, '', :is_admin)
    """), {
        "username": username, "nickname": nickname, "password": hashed,
        "cellphone": cellphone, "state": state, "gender": gender, "is_admin": is_admin
    })
    await session.commit()
    return {"success": True}


@router.put('/users/{user_id}', name='编辑用户')
async def update_user_by_admin(
    user_id: str,
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    admin: Annotated[UserModel, Depends(require_admin)],
    nickname: str = Body(...),
    cellphone: str = Body(...),
    password: str = Body(''),
    gender: str = Body('unknown'),
    is_admin: bool = Body(False),
    enabled: bool = Body(True),
):
    from app.support.password_helper import get_password_hash

    # 检查手机号是否被其他用户占用
    exists_phone = await session.execute(
        text("SELECT id FROM users WHERE cellphone = :cellphone AND id != :id"),
        {"cellphone": cellphone, "id": user_id}
    )
    if exists_phone.fetchone():
        raise HTTPException(status_code=400, detail=f'手机号「{cellphone}」已被其他用户注册')

    state = 'enabled' if enabled else 'disabled'

    if password:
        await session.execute(text("""
            UPDATE users SET nickname=:nickname, cellphone=:cellphone, password=:password,
            gender=:gender, is_admin=:is_admin, state=:state WHERE id=:id
        """), {
            "nickname": nickname, "cellphone": cellphone,
            "password": get_password_hash(password),
            "gender": gender, "is_admin": is_admin, "state": state, "id": user_id
        })
    else:
        await session.execute(text("""
            UPDATE users SET nickname=:nickname, cellphone=:cellphone,
            gender=:gender, is_admin=:is_admin, state=:state WHERE id=:id
        """), {
            "nickname": nickname, "cellphone": cellphone,
            "gender": gender, "is_admin": is_admin, "state": state, "id": user_id
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


# ===== 数据管理 =====

@router.get('/data/records', name='价格记录列表')
async def get_price_records(
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    admin: Annotated[UserModel, Depends(require_admin)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    product_name: Optional[str] = Query(None),
):
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
               pr.min_price, pr.max_price, pr.avg_price, p.unit, pr.source
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
    from datetime import datetime
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
    from datetime import datetime

    content = await file.read()
    text_content = content.decode('utf-8-sig')  # 支持带BOM的UTF-8
    reader = csv.DictReader(io.StringIO(text_content))

    saved = 0
    skipped = 0
    errors = []

    for i, row in enumerate(reader, start=2):
        try:
            product_name = row.get('产品名称', '').strip()
            category_name = row.get('分类名称', '').strip()
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

            # 获取或创建分类
            cat_row = await session.execute(
                text("SELECT id FROM categories WHERE name = :name"), {"name": category_name}
            )
            cat = cat_row.fetchone()
            if cat:
                category_id = cat[0]
            else:
                cat_result = await session.execute(
                    text("INSERT INTO categories (name) VALUES (:name) RETURNING id"),
                    {"name": category_name}
                )
                category_id = cat_result.fetchone()[0]

            # 获取或创建产品
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

            # 获取或创建市场
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

            # 插入价格记录
            result = await session.execute(text("""
                INSERT INTO price_records (time, product_id, market_id, price, min_price, max_price, avg_price, source)
                VALUES (:time, :product_id, :market_id, :avg_price, :min_price, :max_price, :avg_price, 'csv')
                ON CONFLICT DO NOTHING
                RETURNING time
            """), {
                "time": record_time, "product_id": product_id, "market_id": market_id,
                "avg_price": avg_price, "min_price": min_price, "max_price": max_price
            })

            if result.fetchone():
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

