"""
Prophet 价格预测模型精度测试
数据来源：PostgreSQL 数据库
测试方法：每个分类选取一个代表产品，前80%训练，后20%测试
指标：MAE、RMSE、MAPE
"""

import pandas as pd
import numpy as np
import warnings
import sys
import psycopg2

sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'agriprice',
    'user': 'postgres',
    'password': '123456',
}

# 每个分类选一个价格规律性较强的代表产品
TEST_PRODUCTS = [
    ('水菜',   '小白菜'),
    ('海水鱼', '带鱼'),
    ('淡水鱼', '鲤鱼'),
    ('牛肉类', '牛腩'),
    ('猪肉类', '白条猪'),
    ('禽蛋类', '肉鸡'),
    ('羊肉类', '去骨羊前腿'),
    ('虾蟹类', '基围虾'),
    ('贝壳类', '花蛤'),
    ('其他类', '柠檬'),
]


# ── 从数据库获取数据 ───────────────────────────────────
def fetch_product_data(product_name):
    conn = psycopg2.connect(**DB_CONFIG)
    sql = """
        SELECT DATE(pr.time AT TIME ZONE 'Asia/Shanghai') AS ds,
               AVG(pr.avg_price) AS y
        FROM price_records pr
        JOIN products p ON p.id = pr.product_id
        WHERE p.name = %s
        GROUP BY DATE(pr.time AT TIME ZONE 'Asia/Shanghai')
        ORDER BY ds ASC
    """
    df = pd.read_sql(sql, conn, params=(product_name,))
    conn.close()
    return df


# ── 指标计算 ──────────────────────────────────────────
def calc_metrics(y_true, y_pred):
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    mae  = np.mean(np.abs(y_true - y_pred))
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
    mask = y_true != 0
    mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
    return round(mae, 4), round(rmse, 4), round(mape, 2)


# ── 单产品测试 ────────────────────────────────────────
def test_product(category, product_name):
    from prophet import Prophet

    df = fetch_product_data(product_name)
    df['ds'] = pd.to_datetime(df['ds'])
    df['y'] = df['y'].astype(float)
    df = df.sort_values('ds').drop_duplicates('ds').reset_index(drop=True)

    if len(df) < 30:
        return None

    split = int(len(df) * 0.8)
    train = df.iloc[:split]
    test  = df.iloc[split:]

    m = Prophet(
        daily_seasonality=False,
        weekly_seasonality=False,
        yearly_seasonality=len(df) >= 730,
        changepoint_prior_scale=0.05,
        holidays_prior_scale=1.0
    )
    m.add_country_holidays(country_name='CN')
    m.fit(df)

    future = m.make_future_dataframe(periods=len(test))
    forecast = m.predict(future)
    forecast = forecast.set_index('ds')

    y_true, y_pred = [], []
    for _, row in test.iterrows():
        if row['ds'] in forecast.index:
            y_true.append(row['y'])
            y_pred.append(forecast.loc[row['ds'], 'yhat'])

    if not y_true:
        return None

    mae, rmse, mape = calc_metrics(y_true, y_pred)
    return {
        '分类':         category,
        '代表产品':     product_name,
        '总条数':       len(df),
        '训练集':       len(train),
        '测试集':       len(test),
        '数据起始':     str(df['ds'].min().date()),
        '数据截止':     str(df['ds'].max().date()),
        'MAE（元/斤）': mae,
        'RMSE（元/斤）': rmse,
        'MAPE（%）':    mape,
    }


# ── 主流程 ────────────────────────────────────────────
def main():
    results = []
    for category, product in TEST_PRODUCTS:
        print(f'测试：{category} - {product} ...', end=' ', flush=True)
        try:
            r = test_product(category, product)
            if r:
                results.append(r)
                print(f"MAE={r['MAE（元/斤）']}  RMSE={r['RMSE（元/斤）']}  MAPE={r['MAPE（%）']}%")
            else:
                print('数据不足，跳过')
        except Exception as e:
            print(f'失败：{e}')

    if not results:
        print('无有效结果')
        return

    result_df = pd.DataFrame(results)
    print('\n========== 测试结果汇总 ==========')
    print(result_df.to_string(index=False))

    avg_mae  = round(result_df['MAE（元/斤）'].mean(), 4)
    avg_rmse = round(result_df['RMSE（元/斤）'].mean(), 4)
    avg_mape = round(result_df['MAPE（%）'].mean(), 2)
    print(f'\n平均值：MAE={avg_mae}  RMSE={avg_rmse}  MAPE={avg_mape}%')

    out_path = 'test/prophet_accuracy_result.csv'
    result_df.to_csv(out_path, index=False, encoding='utf-8-sig')
    print(f'结果已保存至：{out_path}')


if __name__ == '__main__':
    main()
