"""
Prophet 水菜价格预测精度测试
changepoint_prior_scale=0.5
测试方法：前80%训练，后20%测试
指标：MAE、RMSE、MAPE
"""

import pandas as pd
import numpy as np
import warnings
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

from prophet import Prophet

DATA_PATH = os.path.join(os.path.dirname(__file__), '数据集', '水菜报价.xlsx')


def calc_metrics(y_true, y_pred):
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    mae  = np.mean(np.abs(y_true - y_pred))
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
    mask = y_true != 0
    mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
    return round(mae, 4), round(rmse, 4), round(mape, 2)


def test_product(product_name):
    df_raw = pd.read_excel(DATA_PATH)
    df = df_raw[df_raw['产品名称'] == product_name][['日期', '均价']].copy()
    df.columns = ['ds', 'y']
    df['ds'] = pd.to_datetime(df['ds'])
    df = df.groupby('ds')['y'].mean().reset_index()
    df = df.sort_values('ds').reset_index(drop=True)

    if len(df) < 30:
        return None

    split = int(len(df) * 0.8)
    train = df.iloc[:split]
    test  = df.iloc[split:]

    m = Prophet(
        changepoint_prior_scale=0.5,
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=len(train) >= 365,
    )
    m.fit(train)

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
        '产品名称':      product_name,
        '总条数':        len(df),
        '训练集':        len(train),
        '测试集':        len(test),
        'MAE（元/斤）':  mae,
        'RMSE（元/斤）': rmse,
        'MAPE（%）':     mape,
    }


def main():
    df_raw = pd.read_excel(DATA_PATH)
    products = df_raw['产品名称'].unique()

    results = []
    for p in products:
        print(f'测试：{p} ...', end=' ', flush=True)
        try:
            r = test_product(p)
            if r:
                results.append(r)
                print(f"MAE={r['MAE（元/斤）']}  RMSE={r['RMSE（元/斤）']}  MAPE={r['MAPE（%）']}%")
            else:
                print('数据不足')
        except Exception as e:
            print(f'失败：{e}')

    result_df = pd.DataFrame(results)
    print('\n========== 水菜预测精度汇总 ==========')
    print(result_df.to_string(index=False))

    avg_mae  = round(result_df['MAE（元/斤）'].mean(), 4)
    avg_rmse = round(result_df['RMSE（元/斤）'].mean(), 4)
    avg_mape = round(result_df['MAPE（%）'].mean(), 2)
    print(f'\n平均值：MAE={avg_mae}  RMSE={avg_rmse}  MAPE={avg_mape}%')

    out = os.path.join(os.path.dirname(__file__), 'prophet_shuicai_result.csv')
    result_df.to_csv(out, index=False, encoding='utf-8-sig')
    print(f'结果已保存至：{out}')


if __name__ == '__main__':
    main()
