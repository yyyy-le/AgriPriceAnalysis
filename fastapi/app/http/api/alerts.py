from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.http.deps import database_deps, auth_deps
from app.models.user import UserModel

router = APIRouter(prefix='/alerts', tags=['价格预警'])


@router.get('/list', name='获取用户预警列表')
async def get_alerts(
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    user: Annotated[UserModel, Depends(auth_deps.get_auth_user)],
):
    sql = """
        SELECT pa.id, pa.product_id, p.name as product_name, pa.alert_type,
               pa.threshold, pa.is_active, pa.created_at, pa.updated_at
        FROM price_alerts pa
        JOIN products p ON pa.product_id = p.id
        WHERE pa.user_id = :user_id
        ORDER BY pa.created_at DESC
    """
    rows = await session.execute(text(sql), {"user_id": user.id})
    return [dict(r._mapping) for r in rows]


@router.post('/create', name='创建预警')
async def create_alert(
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    user: Annotated[UserModel, Depends(auth_deps.get_auth_user)],
    product_id: int = Body(...),
    alert_type: str = Body(...),
    threshold: float = Body(...),
):
    if alert_type not in ('above', 'below'):
        raise HTTPException(status_code=400, detail='alert_type 必须是 above 或 below')

    # 检查产品是否存在
    product = await session.execute(
        text("SELECT id, name FROM products WHERE id = :product_id"),
        {"product_id": product_id}
    )
    product_row = product.fetchone()
    if not product_row:
        raise HTTPException(status_code=404, detail='产品不存在')

    # 创建预警
    sql = """
        INSERT INTO price_alerts (user_id, product_id, alert_type, threshold)
        VALUES (:user_id, :product_id, :alert_type, :threshold)
        RETURNING id
    """
    result = await session.execute(text(sql), {
        "user_id": user.id,
        "product_id": product_id,
        "alert_type": alert_type,
        "threshold": threshold
    })
    await session.commit()
    alert_id = result.scalar()

    # 立即检查今天的价格数据
    price_sql = """
        SELECT avg_price, time
        FROM price_records
        WHERE product_id = :product_id
          AND DATE(time) = CURRENT_DATE
        ORDER BY time DESC
        LIMIT 1
    """
    price_result = await session.execute(text(price_sql), {"product_id": product_id})
    price_row = price_result.fetchone()

    triggered = False
    if price_row:
        current_price = float(price_row.avg_price)

        # 判断是否触发预警
        if alert_type == "above" and current_price > threshold:
            triggered = True
        elif alert_type == "below" and current_price < threshold:
            triggered = True

        if triggered:
            # 记录预警日志
            log_sql = """
                INSERT INTO alert_logs
                (alert_id, price_value, threshold_value, alert_type, product_name)
                VALUES (:alert_id, :price_value, :threshold_value, :alert_type, :product_name)
            """
            await session.execute(text(log_sql), {
                "alert_id": alert_id,
                "price_value": current_price,
                "threshold_value": threshold,
                "alert_type": alert_type,
                "product_name": product_row.name
            })
            await session.commit()

    return {
        "id": alert_id,
        "success": True,
        "triggered": triggered,
        "message": "预警已创建" + ("，今日价格已触发预警" if triggered else "")
    }


@router.put('/update/{alert_id}', name='更新预警')
async def update_alert(
    alert_id: int,
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    user: Annotated[UserModel, Depends(auth_deps.get_auth_user)],
    alert_type: Optional[str] = Body(None),
    threshold: Optional[float] = Body(None),
    is_active: Optional[bool] = Body(None),
    created_at: Optional[str] = Body(None),
):
    # 检查预警是否属于当前用户
    check = await session.execute(
        text("SELECT id FROM price_alerts WHERE id = :alert_id AND user_id = :user_id"),
        {"alert_id": alert_id, "user_id": user.id}
    )
    if not check.fetchone():
        raise HTTPException(status_code=404, detail='预警不存在或无权限')

    updates = []
    params = {"alert_id": alert_id}

    if alert_type is not None:
        if alert_type not in ('above', 'below'):
            raise HTTPException(status_code=400, detail='alert_type 必须是 above 或 below')
        updates.append("alert_type = :alert_type")
        params["alert_type"] = alert_type

    if threshold is not None:
        updates.append("threshold = :threshold")
        params["threshold"] = threshold

    if is_active is not None:
        updates.append("is_active = :is_active")
        params["is_active"] = is_active

    if created_at is not None:
        updates.append("created_at = :created_at")
        params["created_at"] = created_at

    if not updates:
        return {"success": True}

    updates.append("updated_at = NOW()")
    sql = f"UPDATE price_alerts SET {', '.join(updates)} WHERE id = :alert_id"
    await session.execute(text(sql), params)
    await session.commit()
    return {"success": True}


@router.delete('/delete/{alert_id}', name='删除预警')
async def delete_alert(
    alert_id: int,
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    user: Annotated[UserModel, Depends(auth_deps.get_auth_user)],
):
    result = await session.execute(
        text("DELETE FROM price_alerts WHERE id = :alert_id AND user_id = :user_id RETURNING id"),
        {"alert_id": alert_id, "user_id": user.id}
    )
    await session.commit()
    if not result.fetchone():
        raise HTTPException(status_code=404, detail='预警不存在或无权限')
    return {"success": True}


@router.get('/logs', name='获取预警历史记录')
async def get_alert_logs(
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    user: Annotated[UserModel, Depends(auth_deps.get_auth_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    offset = (page - 1) * page_size

    sql = """
        SELECT al.id, al.triggered_at, al.price_value, al.threshold_value,
               al.alert_type, al.product_name, al.is_read
        FROM alert_logs al
        JOIN price_alerts pa ON al.alert_id = pa.id
        WHERE pa.user_id = :user_id
        ORDER BY al.triggered_at DESC
        LIMIT :limit OFFSET :offset
    """
    count_sql = """
        SELECT COUNT(*)
        FROM alert_logs al
        JOIN price_alerts pa ON al.alert_id = pa.id
        WHERE pa.user_id = :user_id
    """

    rows = await session.execute(text(sql), {
        "user_id": user.id,
        "limit": page_size,
        "offset": offset
    })
    total = await session.execute(text(count_sql), {"user_id": user.id})

    return {
        "total": total.scalar(),
        "page": page,
        "page_size": page_size,
        "list": [dict(r._mapping) for r in rows]
    }


@router.post('/logs/{log_id}/mark-read', name='标记预警记录为已读')
async def mark_log_read(
    log_id: int,
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    user: Annotated[UserModel, Depends(auth_deps.get_auth_user)],
):
    # 检查记录是否属于当前用户
    check = await session.execute(text("""
        SELECT al.id FROM alert_logs al
        JOIN price_alerts pa ON al.alert_id = pa.id
        WHERE al.id = :log_id AND pa.user_id = :user_id
    """), {"log_id": log_id, "user_id": user.id})

    if not check.fetchone():
        raise HTTPException(status_code=404, detail='记录不存在或无权限')

    await session.execute(
        text("UPDATE alert_logs SET is_read = TRUE WHERE id = :log_id"),
        {"log_id": log_id}
    )
    await session.commit()
    return {"success": True}
