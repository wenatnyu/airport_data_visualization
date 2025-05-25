import openpyxl
import pandas as pd
from datetime import datetime, timedelta
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

# 读取 Excel 文件，使用data_only=True来获取公式计算后的值
file_path = "./uploads/raw_data.xlsx"
wb = openpyxl.load_workbook(file_path, data_only=True)
sheet = wb.active

# 从工作表名称获取年份
sheet_name = sheet.title
year = int(sheet_name[:-1])  # 假设工作表名称就是年份
print(f"Sheet name: {sheet_name}, Year: {year}")

# 创建一个新的工作表来存储处理后的数据
new_sheet = wb.create_sheet("Processed")

# 复制所有数据到新工作表，同时处理合并单元格和日期
for row in sheet.iter_rows():
    for cell in row:
        # 获取单元格的值（此时已经是计算后的值）
        value = cell.value
        print(f"Processing cell: {cell.coordinate}, Value: {value}, Type: {type(value)}")
        
        # 如果单元格是合并单元格的一部分，获取合并区域的值
        if isinstance(cell, openpyxl.cell.cell.MergedCell):
            for merged_range in sheet.merged_cells.ranges:
                if cell.coordinate in merged_range:
                    value = sheet.cell(merged_range.min_row, merged_range.min_col).value
                    print(f"Found merged cell value: {value}")
                    break
        
        # 如果是A列（第一列），处理日期
        if cell.column == 1 and value is not None:
            print(f"Processing date in column A: {value}")
            try:
                # 处理Excel数字日期格式
                if isinstance(value, (int, float)):
                    # Excel的日期是从1900年1月1日开始的天数
                    excel_date = datetime(1900, 1, 1) + timedelta(days=int(value)-2)  # -2 是因为Excel的日期系统有一个bug
                    # 只保留月日信息
                    value = excel_date.strftime('%m-%d')
                    print(f"Converted Excel date: {value}")
                # 处理字符串日期格式
                elif isinstance(value, str):
                    print(f"Value is string: {value}")
                    # 使用正则表达式提取月和日
                    match = re.match(r'(\d+)月(\d+)日', value)
                    if match:
                        month = int(match.group(1))
                        day = int(match.group(2))
                        print(f"Matched month: {month}, day: {day}")
                        # 创建完整日期
                        full_date = datetime(year, month, day)
                        value = full_date.strftime('%Y-%m-%d')
                        print(f"Converted date: {value}")
                    else:
                        print(f"No match found for pattern in: {value}")
                else:
                    print(f"Value is not string or number: {type(value)}")
            except (ValueError, TypeError) as err:
                # 如果日期解析失败，保持原值
                print(f"Error processing date: {err}")
                pass
        
        # 将值写入新工作表
        new_sheet.cell(row=cell.row, column=cell.column, value=value)

# 删除原始工作表并重命名新工作表
wb.remove(sheet)
new_sheet.title = "Sheet1"

# 转换为 DataFrame
data = []
for row in new_sheet.iter_rows(values_only=True):
    data.append(row)

df = pd.DataFrame(data)

# 导出为 CSV
df.to_csv("./uploads/raw_data.csv", index=False, header=False if "不需要表头" else True)

# 导出为 JSON
df.to_json("./uploads/raw_data.json", orient="records", indent=2)

print("处理完成！")