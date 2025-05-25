import pandas as pd
import numpy as np
import re

def evaluate_formula(value):
    try:
        # 如果不是字符串或不包含运算符，直接返回原值
        if not isinstance(value, str) or not any(op in value for op in ['+', '-', '*', '/']):
            return value
            
        # 替换中文数字
        chinese_nums = {'一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
                       '六': '6', '七': '7', '八': '8', '九': '9', '零': '0'}
        for cn, num in chinese_nums.items():
            value = value.replace(cn, num)
        
        # 移除除数字和运算符外的所有字符
        value = re.sub(r'[^0-9+\-*/().]', '', value)
        
        # 计算公式
        return eval(value)
    except:
        return value

def process_airport_data(input_file, output_file):
    # 读取CSV文件
    df = pd.read_csv(input_file, header=None)
    
    # 找到包含机场名称的行（第一行包含'昆明长水'或类似）
    airport_row = df[df[0].str.contains('昆明长水', na=False)].index[0]
    
    # 从机场名称行开始获取数据
    df = df.iloc[airport_row:]
    
    # 重置索引
    df = df.reset_index(drop=True)
    
    # 删除所有列都为空的行
    df = df.dropna(how='all')
    
    # 对所有列应用公式计算
    for col in df.columns:
        df[col] = df[col].apply(evaluate_formula)
    
    # 保存处理后的数据
    df.to_csv(output_file, index=False, header=False)

if __name__ == "__main__":
    input_file = "./uploads/raw_data.csv"
    output_file = "./uploads/processed_airport_data.csv"
    process_airport_data(input_file, output_file) 