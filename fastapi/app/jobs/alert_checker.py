import asyncio
import logging
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.providers.database_provider import async_session_factory

logger = logging.getLogger(__name__)


async def check_price_alerts():
    """
    定期检查价格预警
    每次运行时检查所有启用的预警规则，对比最新价格数据
    """
    logger.info("[价格预警] 开始检查价格预警...")

    async with async_session_factory() as session:
        try:
            # 获取所有启用的预警规则
            alerts_sql = """
                SELECT pa.id, pa.user_id, pa.product_id, pa.alert_type, pa.threshold,
                       p.name as product_name
                FROM price_alerts pa
                JOIN products p ON pa.product_id = p.id
                WHERE pa.is_active = TRUE
            """
            alerts_result = await session.execute(text(alerts_sql))
            alerts = [dict(r._mapping) for r in alerts_result]

            if not alerts:
                logger.info("[价格预警] 没有启用的预警规则")
                return

            logger.info(f"[价格预警] 找到 {len(alerts)} 条启用的预警规则")

            triggered_count = 0

            for alert in alerts:
                # 获取该产品的最新价格记录
                price_sql = """
                    SELECT avg_price, time
                    FROM price_records
                    WHERE product_id = :product_id
                    ORDER BY time DESC
                    LIMIT 1
                """
                price_result = await session.execute(
                    text(price_sql),
                    {"product_id": alert["product_id"]}
                )
                price_row = price_result.fetchone()

                if not price_row:
                    continue

                current_price = float(price_row.avg_price)
                threshold = float(alert["threshold"])
                alert_type = alert["alert_type"]

                # 判断是否触发预警
                triggered = False
                if alert_type == "above" and current_price > threshold:
                    triggered = True
                elif alert_type == "below" and current_price < threshold:
                    triggered = True

                if triggered:
                    # 检查是否在最近1小时内已经触发过相同预警（避免重复通知）
                    check_recent_sql = """
                        SELECT id FROM alert_logs
                        WHERE alert_id = :alert_id
                          AND triggered_at > NOW() - INTERVAL '1 hour'
                        LIMIT 1
                    """
                    recent = await session.execute(
                        text(check_recent_sql),
                        {"alert_id": alert["id"]}
                    )

                    if recent.fetchone():
                        logger.debug(f"[价格预警] 预警 {alert['id']} 最近1小时内已触发，跳过")
                        continue

                    # 记录预警日志
                    log_sql = """
                        INSERT INTO alert_logs
                        (alert_id, price_value, threshold_value, alert_type, product_name)
                        VALUES (:alert_id, :price_value, :threshold_value, :alert_type, :product_name)
                    """
                    await session.execute(text(log_sql), {
                        "alert_id": alert["id"],
                        "price_value": current_price,
                        "threshold_value": threshold,
                        "alert_type": alert_type,
                        "product_name": alert["product_name"]
                    })

                    triggered_count += 1
                    logger.info(
                        f"[价格预警] 触发预警: {alert['product_name']} "
                        f"当前价格 {current_price} 元 "
                        f"{'>' if alert_type == 'above' else '<'} "
                        f"阈值 {threshold} 元"
                    )

            await session.commit()
            logger.info(f"[价格预警] 检查完成，触发 {triggered_count} 条预警")

        except Exception as e:
            logger.error(f"[价格预警] 检查失败: {e}", exc_info=True)
            await session.rollback()


async def start_alert_checker():
    """
    启动价格预警检查器，每10分钟检查一次
    """
    logger.info("[价格预警] 预警检查器已启动，每10分钟检查一次")

    while True:
        try:
            await check_price_alerts()
        except Exception as e:
            logger.error(f"[价格预警] 检查器异常: {e}", exc_info=True)

        # 等待10分钟
        await asyncio.sleep(600)
