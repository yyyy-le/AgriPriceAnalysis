from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
import httpx
import json

from app.http.deps import database_deps, auth_deps
from app.models.user import UserModel
from config.ai import settings as ai_settings

router = APIRouter(prefix='/ai', tags=['AI助手'])


class ChatRequest(BaseModel):
    message: str


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_latest_prices",
            "description": "获取最新一天的农产品价格数据，用于回答今天价格、最新价格、现在多少钱等问题",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "产品名称关键词，如大白菜、苹果，为空则返回所有产品"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回条数，默认20",
                        "default": 20
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_price_history",
            "description": "查询某个农产品在指定时间段内的历史价格，用于回答X天前价格、上个月价格、某段时间价格趋势等问题",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "产品名称，如大白菜"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "开始日期，格式YYYY-MM-DD"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "结束日期，格式YYYY-MM-DD"
                    }
                },
                "required": ["product_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_price_ranking",
            "description": "获取价格排行榜，用于回答最贵的是什么、最便宜的是什么、哪个最划算等问题",
            "parameters": {
                "type": "object",
                "properties": {
                    "order": {
                        "type": "string",
                        "enum": ["asc", "desc"],
                        "description": "asc=从低到高最便宜，desc=从高到低最贵"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回条数，默认10",
                        "default": 10
                    }
                },
                "required": ["order"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_price_volatility",
            "description": "获取价格波动最大的产品，用于回答最近涨价最厉害、价格最不稳定等问题",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "统计天数，默认7天",
                        "default": 7
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回条数，默认10",
                        "default": 10
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_products",
            "description": "对比多个产品的价格，用于回答大白菜和圆白菜哪个贵、对比这几个产品价格等问题",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "要对比的产品名称列表"
                    }
                },
                "required": ["product_names"]
            }
        }
    }
]


async def execute_tool(tool_name: str, args: dict, session: AsyncSession) -> str:
    try:
        if tool_name == "get_latest_prices":
            product_name = args.get("product_name", "")
            limit = args.get("limit", 20)
            where = "WHERE DATE(pr.time) = (SELECT DATE(MAX(time)) FROM price_records)"
            params = {"limit": limit}
            if product_name:
                where += " AND p.name ILIKE :keyword"
                params["keyword"] = f"%{product_name}%"
            sql = f"""
                SELECT p.name as product_name, c.name as category_name,
                       pr.avg_price, pr.min_price, pr.max_price, p.unit, DATE(pr.time) as date
                FROM price_records pr
                JOIN products p ON pr.product_id = p.id
                JOIN categories c ON p.category_id = c.id
                {where}
                ORDER BY p.name
                LIMIT :limit
            """
            rows = await session.execute(text(sql), params)
            data = [dict(r._mapping) for r in rows]
            if not data:
                return f"未找到{'「' + product_name + '」' if product_name else ''}的价格数据"
            date = data[0]['date']
            result = [f"【{date} 价格数据】"]
            for item in data:
                result.append(
                    f"- {item['product_name']}（{item['category_name']}）："
                    f"均价{item['avg_price']}元/{item['unit']}，"
                    f"最低{item['min_price']}，最高{item['max_price']}"
                )
            return "\n".join(result)

        elif tool_name == "get_price_history":
            product_name = args.get("product_name", "")
            start_date = args.get("start_date", "")
            end_date = args.get("end_date", "")
            params = {"keyword": f"%{product_name}%"}
            where_extra = ""
            if start_date:
                where_extra += " AND DATE(pr.time) >= :start_date"
                params["start_date"] = start_date
            if end_date:
                where_extra += " AND DATE(pr.time) <= :end_date"
                params["end_date"] = end_date
            sql = f"""
                SELECT DATE(pr.time) as date, p.name as product_name, p.unit,
                       ROUND(AVG(pr.avg_price)::numeric, 2) as avg_price,
                       ROUND(MIN(pr.min_price)::numeric, 2) as min_price,
                       ROUND(MAX(pr.max_price)::numeric, 2) as max_price
                FROM price_records pr
                JOIN products p ON pr.product_id = p.id
                WHERE p.name ILIKE :keyword {where_extra}
                GROUP BY DATE(pr.time), p.name, p.unit
                ORDER BY date DESC
                LIMIT 30
            """
            rows = await session.execute(text(sql), params)
            data = [dict(r._mapping) for r in rows]
            if not data:
                return f"未找到「{product_name}」在该时间段的价格数据"
            result = [f"【{product_name} 历史价格】"]
            for item in data:
                result.append(
                    f"- {item['date']}：均价{item['avg_price']}元/{item['unit']}，"
                    f"最低{item['min_price']}，最高{item['max_price']}"
                )
            return "\n".join(result)

        elif tool_name == "get_price_ranking":
            order = args.get("order", "asc")
            limit = args.get("limit", 10)
            sql = f"""
                SELECT p.name as product_name, p.unit,
                       ROUND(AVG(pr.avg_price)::numeric, 2) as avg_price
                FROM price_records pr
                JOIN products p ON pr.product_id = p.id
                WHERE DATE(pr.time) = (SELECT DATE(MAX(time)) FROM price_records)
                GROUP BY p.name, p.unit
                ORDER BY avg_price {order}
                LIMIT :limit
            """
            rows = await session.execute(text(sql), {"limit": limit})
            data = [dict(r._mapping) for r in rows]
            if not data:
                return "暂无价格数据"
            label = "最便宜" if order == "asc" else "最贵"
            result = [f"【今日{label}产品 Top{limit}】"]
            for i, item in enumerate(data, 1):
                result.append(f"{i}. {item['product_name']}：{item['avg_price']}元/{item['unit']}")
            return "\n".join(result)

        elif tool_name == "get_price_volatility":
            days = args.get("days", 7)
            limit = args.get("limit", 10)
            sql = f"""
                SELECT p.name as product_name,
                       ROUND(((MAX(pr.max_price) - MIN(pr.min_price)) / NULLIF(AVG(pr.avg_price), 0) * 100)::numeric, 1) as volatility,
                       ROUND(AVG(pr.avg_price)::numeric, 2) as avg_price
                FROM price_records pr
                JOIN products p ON pr.product_id = p.id
                WHERE pr.time >= NOW() - INTERVAL '{days} days'
                GROUP BY p.name
                HAVING AVG(pr.avg_price) > 0
                ORDER BY volatility DESC
                LIMIT :limit
            """
            rows = await session.execute(text(sql), {"limit": limit})
            data = [dict(r._mapping) for r in rows]
            if not data:
                return "暂无波动数据"
            result = [f"【近{days}天价格波动最大 Top{limit}】"]
            for i, item in enumerate(data, 1):
                result.append(
                    f"{i}. {item['product_name']}：波动率{item['volatility']}%，均价{item['avg_price']}元"
                )
            return "\n".join(result)

        elif tool_name == "compare_products":
            product_names = args.get("product_names", [])
            if not product_names:
                return "请提供要对比的产品名称"
            results = []
            for name in product_names:
                sql = """
                    SELECT p.name as product_name, p.unit,
                           ROUND(AVG(pr.avg_price)::numeric, 2) as avg_price,
                           ROUND(MIN(pr.min_price)::numeric, 2) as min_price,
                           ROUND(MAX(pr.max_price)::numeric, 2) as max_price
                    FROM price_records pr
                    JOIN products p ON pr.product_id = p.id
                    WHERE p.name ILIKE :keyword
                      AND DATE(pr.time) = (SELECT DATE(MAX(time)) FROM price_records)
                    GROUP BY p.name, p.unit
                    LIMIT 1
                """
                rows = await session.execute(text(sql), {"keyword": f"%{name}%"})
                row = rows.fetchone()
                if row:
                    d = dict(row._mapping)
                    results.append(
                        f"- {d['product_name']}：均价{d['avg_price']}元/{d['unit']}，"
                        f"最低{d['min_price']}，最高{d['max_price']}"
                    )
                else:
                    results.append(f"- {name}：暂无数据")
            return "【价格对比】\n" + "\n".join(results)

        return "未知函数"

    except Exception as e:
        return f"查询出错：{str(e)}"


@router.post('/chat', name='AI智能问答')
async def chat(
    request: ChatRequest,
    session: Annotated[AsyncSession, Depends(database_deps.get_db)],
    user: Annotated[UserModel, Depends(auth_deps.get_auth_user)],
):
    system_prompt = """你是一个农产品价格分析助手，同时也是一个友好的通用助手。

【能力说明】
你可以通过调用工具函数查询实时数据库来回答价格相关问题，包括：
- 查询今日最新价格
- 查询历史某一天或某段时间的价格
- 获取价格排行榜（最贵/最便宜）
- 分析价格波动情况
- 对比多个产品价格

【回答原则】
1. 价格相关问题：先调用合适的工具函数查询数据，再根据返回数据回答，数据要具体准确
2. 农业知识问题（种植、养殖、施肥等）：用专业知识直接回答
3. 农产品相关问题（保存、烹饪、营养等）：友好详细地回答
4. 其他问题：正常回答，不拒绝
5. 回答简洁清晰，使用中文，语气自然友好"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": request.message},
    ]

    async def generate():
        async with httpx.AsyncClient(timeout=60) as client:
            for _ in range(5):
                response = await client.post(
                    f'{ai_settings.DEEPSEEK_BASE_URL}/chat/completions',
                    headers={
                        'Authorization': f'Bearer {ai_settings.DEEPSEEK_API_KEY}',
                        'Content-Type': 'application/json',
                    },
                    json={
                        'model': ai_settings.DEEPSEEK_MODEL,
                        'messages': messages,
                        'tools': TOOLS,
                        'tool_choice': 'auto',
                        'max_tokens': 1500,
                    }
                )
                result = response.json()

                if 'error' in result:
                    error_msg = result['error'].get('message', '未知错误')
                    if 'Balance' in error_msg or 'balance' in error_msg:
                        yield '抱歉，AI 服务余额不足，请联系管理员充值。'
                    else:
                        yield f'抱歉，AI 服务出现错误：{error_msg}'
                    break

                choice = result['choices'][0]
                msg = choice['message']

                if choice['finish_reason'] == 'tool_calls' and msg.get('tool_calls'):
                    messages.append(msg)
                    for tool_call in msg['tool_calls']:
                        tool_name = tool_call['function']['name']
                        tool_args = json.loads(tool_call['function']['arguments'])
                        yield f"[QUERYING]{tool_name}\n"
                        tool_result = await execute_tool(tool_name, tool_args, session)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call['id'],
                            "content": tool_result,
                        })
                    continue

                elif choice['finish_reason'] in ('stop', 'length'):
                    async with client.stream(
                        'POST',
                        f'{ai_settings.DEEPSEEK_BASE_URL}/chat/completions',
                        headers={
                            'Authorization': f'Bearer {ai_settings.DEEPSEEK_API_KEY}',
                            'Content-Type': 'application/json',
                        },
                        json={
                            'model': ai_settings.DEEPSEEK_MODEL,
                            'messages': messages,
                            'stream': True,
                            'max_tokens': 1500,
                        }
                    ) as stream_response:
                        async for chunk in stream_response.aiter_bytes():
                            # 解析 SSE 格式：data: {...}\n\n
                            text = chunk.decode('utf-8', errors='ignore')
                            for line in text.split('\n'):
                                line = line.strip()
                                if not line.startswith('data:'):
                                    continue
                                data = line[5:].strip()
                                if data == '[DONE]':
                                    break
                                try:
                                    obj = json.loads(data)
                                    content = obj['choices'][0]['delta'].get('content', '')
                                    if content:
                                        yield content
                                except Exception:
                                    continue
                    break

    return StreamingResponse(generate(), media_type='text/plain; charset=utf-8')