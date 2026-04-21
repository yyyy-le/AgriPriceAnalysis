import os
import pandas as pd

# ===================== 配置 =====================
CSV_FOLDER = r"G:\个人\AgriPriceAnalysis\test\shujuji"  # 使用原始字符串
OUTPUT_FOLDER = "数据集"
# ================================================

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

if not os.path.exists(CSV_FOLDER):
    print(f"Error: Folder '{CSV_FOLDER}' does not exist!")
else:
    csv_files = [f for f in os.listdir(CSV_FOLDER) if f.lower().endswith(".csv")]

    if not csv_files:
        print("No CSV files found in the folder.")
    else:
        for filename in csv_files:
            print("Processing:", filename)
            csv_path = os.path.join(CSV_FOLDER, filename)

            # 尝试多种编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030']
            df = None
            for enc in encodings:
                try:
                    df = pd.read_csv(csv_path, encoding=enc)
                    break
                except UnicodeDecodeError:
                    continue

            if df is None:
                print(f"  Warning: Cannot decode {filename}, skipping...")
                continue

            # 重新整理表头
            new_df = pd.DataFrame()
            new_df["产品名称"] = df["品名"]
            new_df["一级分类"] = df["一级分类"]
            new_df["二级分类"] = df["二级分类"]
            new_df["市场/产地"] = ""
            new_df["均价"] = df["平均价"]
            new_df["最低价"] = df["最低价"]
            new_df["最高价"] = df["最高价"]
            new_df["单位"] = df["单位"]

            # 处理日期
            date_series = pd.to_datetime(df["发布日期"], errors="coerce")
            new_df["日期"] = date_series.apply(
                lambda x: x.strftime("%Y/%m/%d") if pd.notna(x) else ""
            )

            # 保存Excel
            excel_name = os.path.splitext(filename)[0] + ".xlsx"
            excel_path = os.path.join(OUTPUT_FOLDER, excel_name)
            new_df.to_excel(excel_path, index=False, engine="openpyxl")
            print(f"  Saved to: {excel_path} ({len(new_df)} rows)")

        print(f"\nAll done! {len(csv_files)} files processed.")