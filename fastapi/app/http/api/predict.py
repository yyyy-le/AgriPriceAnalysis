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
            f"（{round(float(max(row['yhat_lower'], 0)), 2)}~{round(float(row['yhat_upper']), 2)}）"
        )

    prompt = f"""你是专业农产品市场分析师，请根据以下数据生成简洁的价格分析报告。

【产品】{product_name}（单位：{unit}）
【当前价格】{current_price}元/{unit}
【近30天统计】均价{avg_30}元，最高{max_30}元，最低{min_30}元
【未来{days}天预测】
{chr(10).join(pred_lines)}
【趋势】{days}天后预计{'上涨' if change_pct > 0 else '下跌'}{abs(change_pct)}%

请从三个方面分析（每点2-3句，简洁专业）：
1. 价格走势判断
2. 影响因素分析（季节、供需等）
3. 采购/销售建议"""

    async def generate():
        async with httpx.AsyncClient(timeout=60) as client:
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
                    'max_tokens': 800,
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