"""
CGM 数据适配器 - 支持多种格式
"""

import pandas as pd
from datetime import datetime
from typing import Optional


def parse_wxqi_format(text: str) -> pd.DataFrame:
    """
    解析WXQI/微泰格式 CGM 数据
    
    格式: ID 日期 时间 记录类型 血糖(mmol/L)
    示例: 69137 2024/03/16 12:03 0 15.3
    """
    lines = [l.strip() for l in text.split('\n') if l.strip() and not l.startswith('#')]
    
    # 跳过表头
    data_lines = []
    for line in lines:
        # 检查是否是数据行 (第一列是数字)
        parts = line.split()
        if len(parts) >= 5 and parts[0].isdigit():
            data_lines.append(line)
    
    if not data_lines:
        raise ValueError("No valid data found")
    
    # 解析数据
    data = []
    for line in data_lines:
        parts = line.split()
        if len(parts) >= 5:
            # WXQI格式: ID 日期 时间 记录类型 血糖
            date_str = parts[1]  # 2024/03/16
            time_str = parts[2]  # 12:03
            glucose = float(parts[4])  # mmol/L
            
            timestamp = pd.to_datetime(f"{date_str} {time_str}")
            
            # 转换为 mg/dL
            glucose_mgdl = glucose * 18
            
            data.append({
                'timestamp': timestamp,
                'glucose': glucose_mgdl
            })
    
    df = pd.DataFrame(data)
    return df.sort_values('timestamp')


def parse_standard_format(text: str) -> pd.DataFrame:
    """
    解析标准格式 CGM 数据
    支持: CSV, TSV, 空格分隔
    自动检测分隔符和列名
    """
    lines = [l.strip() for l in text.split('\n') if l.strip() and not l.startswith('#')]
    
    if not lines:
        raise ValueError("Empty data")
    
    # 检测分隔符
    first_line = lines[0]
    if '\t' in first_line:
        sep = '\t'
    elif ',' in first_line:
        sep = ','
    else:
        sep = r'\s+'
    
    # 读取数据
    import io
    try:
        df = pd.read_csv(io.StringIO('\n'.join(lines)), sep=sep)
    except:
        df = pd.read_csv(io.StringIO('\n'.join(lines)), sep=sep, header=None)
    
    cols = df.columns.tolist()
    
    # 智能查找时间列和血糖列
    time_col = None
    glucose_col = None
    
    for col in cols:
        c = str(col).lower()
        if not time_col and any(k in c for k in ['time', 'date', 'timestamp', 'datetime']):
            time_col = col
        if not glucose_col and any(k in c for k in ['glucose', 'value', 'sg', '血糖']):
            glucose_col = col
    
    # 默认：第1列=时间，最后1列=血糖
    if not time_col:
        time_col = cols[0]
    if not glucose_col:
        glucose_col = cols[-1]
    
    # 解析
    df['timestamp'] = pd.to_datetime(df[time_col], errors='coerce')
    df['glucose'] = pd.to_numeric(df[glucose_col], errors='coerce')
    
    # mmol/L 转 mg/dL (值 < 30 说明是 mmol/L)
    if df['glucose'].max() < 30:
        df['glucose'] = df['glucose'] * 18
    
    df = df.dropna(subset=['glucose', 'timestamp'])
    return df.sort_values('timestamp')


def parse_cgm_data(text: str) -> pd.DataFrame:
    """
    自动检测并解析 CGM 数据
    尝试多种格式
    """
    # 尝试 WXQI 格式 (中国常见)
    try:
        return parse_wxqi_format(text)
    except:
        pass
    
    # 尝试标准格式
    try:
        return parse_standard_format(text)
    except Exception as e:
        raise ValueError(f"无法解析数据: {str(e)}")
