import pandas as pd
import numpy as np

def process_csv():
    # 读取CSV文件
    df = pd.read_csv("./uploads/processed_airport_data.csv", header=None)
    
    # 统计每行的非空值数量
    row_counts = df.count(axis=1)
    
    # 输出原始统计信息
    print("\n原始统计信息：")
    print("-" * 30)
    print(f"总行数: {len(df)}")
    print(f"最大列数: {df.shape[1]}")
    print(f"最小每行值数: {row_counts.min()}")
    print(f"最大每行值数: {row_counts.max()}")
    print(f"平均每行值数: {row_counts.mean():.2f}")
    
    # 1. 只保留有120个值的行
    valid_rows = row_counts == 120
    df = df[valid_rows]
    
    # 2. 处理每行末尾多余的逗号
    # 首先找到每行最后一个非空值的列索引
    last_valid_cols = df.apply(lambda x: x.last_valid_index(), axis=1)
    
    # 对每行进行处理
    for idx in df.index:
        last_col = last_valid_cols[idx]
        if last_col is not None:
            # 将最后一个非空值之后的所有列设为NaN
            df.loc[idx, last_col+1:] = np.nan
    
    # 输出处理后的统计信息
    print("\n处理后的统计信息：")
    print("-" * 30)
    print(f"保留的行数: {len(df)}")
    print(f"每行值数: 120")
    
    # 保存处理后的文件
    df.to_csv("./uploads/processed_airport_data.csv", index=False, header=False)
    print("\n文件已保存到 ./uploads/processed_airport_data.csv")

if __name__ == "__main__":
    process_csv() 