from typing import Annotated
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import pandas as pd
import json
import httpx
import warnings

from app.http.deps import database_deps, auth_deps
from app.models.user import UserModel
from config.ai import settings as ai_settings

router = APIRouter(prefix='/prices', tags=['价格预测'])


async def _get_predict_data(session, product_id, days):
    """公共预测逻辑，返回历史数据、预测结果、产品信息"""
    sql = """
        SELECT DATE(pr.time) as ds, AVG(pr.avg_price) as y
        FROM price_records pr
        WHERE pr.product_id = :product_id
        GROUP BY DATE(pr.time)
        ORDER BY ds ASC
    """
    rows = await session.execute(text(sql), {"product_id": product_id})
    data = [dict(r._mapping) for r in rows]

    prod = await session.execute(
        text("SELECT name, unit FROM products WHERE id = :id"),
        {"id": product_id}
    )
    prod_row = prod.fetchone()
    product_name = prod_row[0] if prod_row else "未知产品"
    unit = prod_row[1] if prod_row else "元"

    return data, product_name, unit


def _run_prophet(data, days):
    from prophet import Prophet
    warnings.filterwarnings('ignore')

    df = pd.DataFrame(data)
    df['ds'] = pd.to_datetime(df['ds'])
    df['y'] = df['y'].astype(float)

    m = Prophet(
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=len(df) >= 365,
        changepoint_prior_scale=0.05,
    )
    m.fit(df)

    future = m.make_future_dataframe(periods=days)
    forecast = m.predict(future)

    last_date = df['ds'].max()
    future_fc = forecast[forecast['ds'] > last_date][['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

    return df, future_fc


@router.get('/predict', name='价格预测数据')
async def predict_price(
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    user: Annotated[UserModel, Depends(auth_deps.get_auth_user)],
    product_id: int = Query(...),
    days: int = Query(7, ge=3, le=30),
):
    data, product_name, unit = await _get_predict_data(session, product_id, days)

    if len(data) < 7:
        return {"error": "数据不足，至少需要7天历史数据才能预测"}

    df, future_fc = _run_prophet(data, days)

    current_price = round(float(df['y'].iloc[-1]), 2)
    last_pred = round(float(future_fc['yhat'].iloc[-1]), 2)
    change_pct = round((last_pred - current_price) / current_price * 100, 2)

    history = []
    for _, row in df.tail(30).iterrows():
        history.append({
            "date": row['ds'].strftime('%Y-%m-%d'),
            "price": round(float(row['y']), 2),
        })

    predictions = []
    for _, row in future_fc.iterrows():
        predictions.append({
            "date": row['ds'].strftime('%Y-%m-%d'),
            "predicted_price": round(float(row['yhat']), 2),
            "lower_bound": round(float(max(row['yhat_lower'], 0)), 2),
            "upper_bound": round(float(row['yhat_upper']), 2),
        })

    return {
        "product_name": product_name,
        "unit": unit,
        "current_price": current_price,
        "history": history,
        "predictions": predictions,
        "change_pct": change_pct,
        "trend": "上涨" if change_pct > 0 else "下跌",
    }


@router.get('/predict/analysis', name='AI价格分析报告')
async def predict_analysis(
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    user: Annotated[UserModel, Depends(auth_deps.get_auth_user)],
    product_id: int = Query(...),
    days: int = Query(7, ge=3, le=30),
):
    data, product_name, unit = await _get_predict_data(session, product_id, days)

    async def err_gen(msg):
        yield msg

    if len(data) < 7:
        return StreamingResponse(err_gen("数据不足，无法生成分析报告。"), media_type='text/plain; charset=utf-8')

    df, future_fc = _run_prophet(data, days)

    current_price = round(float(df['y'].iloc[-1]), 2)
    avg_30 = round(float(df['y'].tail(30).mean()), 2)
    max_30 = round(float(df['y'].tail(30).max()), 2)
    min_30 = round(float(df['y'].tail(30).min()), 2)
    last_pred = round(float(future_fc['yhat'].iloc[-1]), 2)
    change_pct = round((last_pred - current_price) / current_price * 100, 2)

    pred_lines = []
    for _, row in future_fc.iterrows():
        pred_lines.append(
            f"{row['ds'].strftime('%m/%d')}：{round(float(row['yhat']), 2)}元"
            f"（区间 {round(float(max(row['yhat_lower'], 0)), 2)}~{round(float(row['yhat_upper']), 2)}）"
        )

    prompt = f"""你是资深农产品市场分析师，拥有多年一线市场经验。请根据以下真实数据，撰写一份详尽、专业的价格分析报告，供采购商、批发商和农户参考决策。

### 数据摘要
- **产品名称**：{product_name}（计量单位：{unit}）
- **当前最新价格**：{current_price} 元/{unit}
- **近30天价格统计**：均价 {avg_30} 元，历史最高 {max_30} 元，历史最低 {min_30} 元，价格区间波动为 {round(max_30 - min_30, 2)} 元
- **未来{days}天逐日预测**：
{chr(10).join(pred_lines)}
- **整体预测趋势**：{days}天后预计价格较当前{'上涨' if change_pct > 0 else '下跌'} {abs(change_pct)}%，达到 {round(current_price * (1 + change_pct/100), 2)} 元/{unit}

---

请按照以下结构撰写详细分析报告，每个章节需充分展开，不少于5句话：

### 一、当前价格走势分析
深入分析当前价格所处的位置（是否处于高位/低位/震荡区间），结合近30天的价格变化曲线，说明价格的阶段性特征。分析价格从近期高点/低点的变化幅度，以及当前价格与历史均价的偏差程度，判断市场是处于上升通道、下跌通道还是横盘整理阶段。

### 二、未来价格趋势预判
结合预测模型给出的逐日数据，详细描述未来{days}天的价格走势路径，指出预计的转折点、加速阶段或企稳时间节点。分析预测置信区间的宽窄，评估预测的可靠性和风险程度，并给出乐观、中性、悲观三种情景下的价格区间。

### 三、影响价格的核心因素
从以下多个维度展开分析：
1. **季节性因素**：当前所处季节对该农产品生长、采收、上市节奏的影响；
2. **供给端分析**：主产区的产量预期、采收进度、库存水平及集中上市压力；
3. **需求端分析**：终端消费需求变化、节假日效应、加工和出口需求的拉动或抑制；
4. **流通与物流**：运输成本、冷链配套、产销区距离对价格的传导影响；
5. **市场竞争**：同类替代品价格走势对本产品的替代效应。

### 四、风险提示与注意事项
明确列出当前市场中存在的主要不确定因素，包括但不限于极端天气风险、政策性调控、疫情或突发事件影响、进出口政策变化等，并评估这些风险对价格的潜在冲击方向和幅度。提醒市场参与者需重点关注哪些预警信号。

### 五、采购与销售操作建议
针对不同角色（采购商/批发商/农户/零售商）给出具体可操作的建议：
- **采购时机**：当前是否适合大量采购，最佳建仓时间窗口在何时；
- **库存策略**：建议的库存周期与库存量，如何规避价格下行风险；
- **销售策略**：农户和批发商应如何把握出货节奏，避免集中踩踏；
- **套期保值**：如有期货或订单农业机会，是否建议锁定远期价格。

---
*本报告基于历史价格数据与预测模型生成，仅供参考，实际市场行情受多重突发因素影响，建议结合实时市场信息综合研判后做出决策。*"""

    async def generate():
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                'POST',
                f'{ai_settings.DEEPSEEK_BASE_URL}/chat/completions',
                headers={
                    'Authorization': f'Bearer {ai_settings.DEEPSEEK_API_KEY}',
                    'Content-Type': 'application/json',
                },
                json={
                    'model': ai_settings.DEEPSEEK_MODEL,
                    'messages': [{"role": "user", "content": prompt}],
                    'stream': True,
                    'max_tokens': 3000,
                }
            ) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith('data: '):
                        d = line[6:]
                        if d == '[DONE]':
                            break
                        try:
                            obj = json.loads(d)
                            content = obj['choices'][0]['delta'].get('content', '')
                            if content:
                                yield content
                        except Exception:
                            continue

    return StreamingResponse(generate(), media_type='text/plain; charset=utf-8')