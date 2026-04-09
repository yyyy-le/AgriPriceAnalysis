import asyncio, aiohttp

async def main():
    params = {"limit": 100, "current": 1, "pubDateStartTime": "", "pubDateEndTime": "", "prodCatid": "", "prodName": ""}
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "http://www.xinfadi.com.cn/priceDetail.html"}
    async with aiohttp.ClientSession() as client:
        async with client.get("http://www.xinfadi.com.cn/getPriceData.html", params=params, headers=headers) as resp:
            data = await resp.json(content_type=None)
            print("count:", data.get("count"))
            print("list长度:", len(data.get("list", [])))

asyncio.run(main())